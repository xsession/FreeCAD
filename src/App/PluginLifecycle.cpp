/***************************************************************************
 *   Copyright (c) 2024 FreeCAD Project                                   *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <regex>

#include <Base/Console.h>
#include <Base/XMLTools.h>
#include <xercesc/parsers/XercesDOMParser.hpp>
#include <xercesc/dom/DOM.hpp>

#include "PluginLifecycle.h"

using namespace App;

// ---------------------------------------------------------------------------
// ApiVersion
// ---------------------------------------------------------------------------

std::string ApiVersion::toString() const
{
    std::ostringstream ss;
    ss << major << "." << minor << "." << patch;
    return ss.str();
}

ApiVersion ApiVersion::parse(const std::string& s)
{
    ApiVersion v;
    std::regex rx(R"((\d+)\.(\d+)(?:\.(\d+))?)");
    std::smatch m;
    if (std::regex_match(s, m, rx)) {
        v.major = std::stoi(m[1].str());
        v.minor = std::stoi(m[2].str());
        if (m[3].matched) {
            v.patch = std::stoi(m[3].str());
        }
    }
    return v;
}

ApiVersion ApiVersion::current()
{
    // Matches the FreeCAD API version — increment when breaking changes occur
    return {1, 0, 0};
}

// ---------------------------------------------------------------------------
// PluginInfo
// ---------------------------------------------------------------------------

CompatResult PluginInfo::checkCompat() const
{
    ApiVersion cur = ApiVersion::current();

    // If apiMin is set and > current, the plugin needs a newer host
    if (apiMin.major > 0 && cur < apiMin) {
        return CompatResult::TooOld;
    }
    // If apiMax is set and < current, the plugin may be too old
    if (apiMax.major > 0 && cur > apiMax) {
        return CompatResult::TooNew;
    }
    return CompatResult::Compatible;
}

// ---------------------------------------------------------------------------
// PluginLifecycle (singleton)
// ---------------------------------------------------------------------------

PluginLifecycle& PluginLifecycle::instance()
{
    static PluginLifecycle inst;
    return inst;
}

bool PluginLifecycle::registerPlugin(const PluginInfo& info)
{
    CompatResult compat = info.checkCompat();
    if (compat == CompatResult::TooOld) {
        Base::Console().Warning(
            "PluginLifecycle: '%s' requires API >= %s (current: %s) — skipping\n",
            info.name.c_str(),
            info.apiMin.toString().c_str(),
            ApiVersion::current().toString().c_str());
        return false;
    }
    if (compat == CompatResult::TooNew) {
        Base::Console().Warning(
            "PluginLifecycle: '%s' max API %s < current %s — may have issues\n",
            info.name.c_str(),
            info.apiMax.toString().c_str(),
            ApiVersion::current().toString().c_str());
        // Still allow registration but warn
    }

    _plugins[info.name] = info;
    _active[info.name] = false;

    fireEvent(info.name, PluginEvent::OnInstall);

    Base::Console().Log("PluginLifecycle: registered '%s' v%s (API %s–%s)\n",
                        info.name.c_str(), info.version.c_str(),
                        info.apiMin.toString().c_str(),
                        info.apiMax.toString().c_str());
    return true;
}

void PluginLifecycle::unregisterPlugin(const std::string& name)
{
    auto it = _plugins.find(name);
    if (it == _plugins.end()) {
        return;
    }
    if (_active[name]) {
        deactivate(name);
    }
    fireEvent(name, PluginEvent::OnUninstall);
    _plugins.erase(it);
    _active.erase(name);
}

bool PluginLifecycle::activate(const std::string& name)
{
    auto it = _plugins.find(name);
    if (it == _plugins.end()) {
        Base::Console().Error("PluginLifecycle: '%s' not registered\n", name.c_str());
        return false;
    }
    if (_active[name]) {
        return true;  // already active
    }

    _active[name] = true;
    fireEvent(name, PluginEvent::OnActivate);
    Base::Console().Log("PluginLifecycle: activated '%s'\n", name.c_str());
    return true;
}

void PluginLifecycle::deactivate(const std::string& name)
{
    auto it = _plugins.find(name);
    if (it == _plugins.end()) {
        return;
    }
    if (!_active[name]) {
        return;
    }
    fireEvent(name, PluginEvent::OnDeactivate);
    _active[name] = false;
    Base::Console().Log("PluginLifecycle: deactivated '%s'\n", name.c_str());
}

void PluginLifecycle::notifyDocumentOpened(Document* /*doc*/)
{
    for (auto& [name, active] : _active) {
        if (active) {
            fireEvent(name, PluginEvent::OnDocumentOpened);
        }
    }
}

void PluginLifecycle::addHook(PluginEvent event, PluginCallback callback)
{
    _hooks[static_cast<int>(event)].push_back(std::move(callback));
}

void PluginLifecycle::clearHooks(PluginEvent event)
{
    _hooks.erase(static_cast<int>(event));
}

const PluginInfo* PluginLifecycle::pluginInfo(const std::string& name) const
{
    auto it = _plugins.find(name);
    return (it != _plugins.end()) ? &it->second : nullptr;
}

std::vector<std::string> PluginLifecycle::pluginNames() const
{
    std::vector<std::string> names;
    names.reserve(_plugins.size());
    for (auto& [name, _] : _plugins) {
        names.push_back(name);
    }
    return names;
}

bool PluginLifecycle::isActive(const std::string& name) const
{
    auto it = _active.find(name);
    return (it != _active.end()) ? it->second : false;
}

void PluginLifecycle::fireEvent(const std::string& pluginName, PluginEvent event)
{
    auto it = _plugins.find(pluginName);
    if (it == _plugins.end()) {
        return;
    }

    auto hookIt = _hooks.find(static_cast<int>(event));
    if (hookIt == _hooks.end()) {
        return;
    }

    for (auto& cb : hookIt->second) {
        try {
            cb(it->second, event);
        }
        catch (const std::exception& e) {
            Base::Console().Error("PluginLifecycle: hook error for '%s': %s\n",
                                  pluginName.c_str(), e.what());
        }
    }
}

PluginInfo PluginLifecycle::parsePackageXml(const std::string& xmlPath)
{
    PluginInfo info;

    try {
        XERCES_CPP_NAMESPACE::XercesDOMParser parser;
        parser.setValidationScheme(
            XERCES_CPP_NAMESPACE::XercesDOMParser::Val_Never);
        parser.parse(xmlPath.c_str());

        auto* doc = parser.getDocument();
        if (!doc) {
            return info;
        }

        auto* root = doc->getDocumentElement();
        if (!root) {
            return info;
        }

        // Helper to get text content of first child element with given tag
        auto getText = [&](const char* tag) -> std::string {
            XMLCh* xmlTag = XERCES_CPP_NAMESPACE::XMLString::transcode(tag);
            auto* nodes = root->getElementsByTagName(xmlTag);
            XERCES_CPP_NAMESPACE::XMLString::release(&xmlTag);
            if (nodes && nodes->getLength() > 0) {
                auto* elem = nodes->item(0);
                if (elem->getTextContent()) {
                    char* val = XERCES_CPP_NAMESPACE::XMLString::transcode(
                        elem->getTextContent());
                    std::string result(val);
                    XERCES_CPP_NAMESPACE::XMLString::release(&val);
                    return result;
                }
            }
            return {};
        };

        info.name = getText("name");
        info.version = getText("version");
        info.description = getText("description");
        info.author = getText("maintainer");

        // Parse <api-version min="..." max="..."/>
        XMLCh* apiTag = XERCES_CPP_NAMESPACE::XMLString::transcode("api-version");
        auto* apiNodes = root->getElementsByTagName(apiTag);
        XERCES_CPP_NAMESPACE::XMLString::release(&apiTag);

        if (apiNodes && apiNodes->getLength() > 0) {
            auto* apiElem = static_cast<XERCES_CPP_NAMESPACE::DOMElement*>(
                apiNodes->item(0));

            XMLCh* minAttr = XERCES_CPP_NAMESPACE::XMLString::transcode("min");
            XMLCh* maxAttr = XERCES_CPP_NAMESPACE::XMLString::transcode("max");

            const XMLCh* minVal = apiElem->getAttribute(minAttr);
            const XMLCh* maxVal = apiElem->getAttribute(maxAttr);

            if (minVal) {
                char* s = XERCES_CPP_NAMESPACE::XMLString::transcode(minVal);
                info.apiMin = ApiVersion::parse(s);
                XERCES_CPP_NAMESPACE::XMLString::release(&s);
            }
            if (maxVal) {
                char* s = XERCES_CPP_NAMESPACE::XMLString::transcode(maxVal);
                info.apiMax = ApiVersion::parse(s);
                XERCES_CPP_NAMESPACE::XMLString::release(&s);
            }

            XERCES_CPP_NAMESPACE::XMLString::release(&minAttr);
            XERCES_CPP_NAMESPACE::XMLString::release(&maxAttr);
        }

        info.path = xmlPath;
    }
    catch (const std::exception& e) {
        Base::Console().Error("PluginLifecycle: failed to parse '%s': %s\n",
                              xmlPath.c_str(), e.what());
    }

    return info;
}
