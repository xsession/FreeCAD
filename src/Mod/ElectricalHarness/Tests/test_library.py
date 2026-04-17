"""Tests for the component library system."""

import json
import unittest

from App.entities import LibraryEntry
from App.library import ComponentLibrary


class TestLibraryBasics(unittest.TestCase):
    def test_add_and_retrieve(self):
        lib = ComponentLibrary()
        entry = LibraryEntry(entry_id="C1", category="Connector", name="2-Pin")
        lib.add_entry(entry)
        self.assertEqual(lib.size, 1)
        self.assertEqual(lib.get_entry("C1").name, "2-Pin")

    def test_remove_entry(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="2-Pin"))
        self.assertTrue(lib.remove_entry("C1"))
        self.assertEqual(lib.size, 0)
        self.assertFalse(lib.remove_entry("C1"))

    def test_all_entries(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="A"))
        lib.add_entry(LibraryEntry(entry_id="C2", category="Wire", name="B"))
        self.assertEqual(len(lib.all_entries()), 2)


class TestLibrarySearch(unittest.TestCase):
    def _lib(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="C1", category="Connector", name="Molex 2-Pin",
            manufacturer="Molex", part_number="39-01-2020", favorite=True,
            is_generic=False,
        ))
        lib.add_entry(LibraryEntry(
            entry_id="C2", category="Connector", name="TE 4-Pin",
            manufacturer="TE Connectivity", part_number="1-480424-0",
            is_generic=False,
        ))
        lib.add_entry(LibraryEntry(
            entry_id="W1", category="Wire", name="22AWG Red",
            is_generic=True, favorite=True,
        ))
        return lib

    def test_search_by_query(self):
        lib = self._lib()
        results = lib.search(query="molex")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry_id, "C1")

    def test_search_by_category(self):
        lib = self._lib()
        results = lib.search(category="Connector")
        self.assertEqual(len(results), 2)

    def test_search_by_manufacturer(self):
        lib = self._lib()
        results = lib.search(manufacturer="TE Connectivity")
        self.assertEqual(len(results), 1)

    def test_search_favorites_only(self):
        lib = self._lib()
        results = lib.search(favorites_only=True)
        self.assertEqual(len(results), 2)

    def test_search_generic_only(self):
        lib = self._lib()
        results = lib.search(generic_only=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry_id, "W1")

    def test_search_combined(self):
        lib = self._lib()
        results = lib.search(query="pin", category="Connector")
        self.assertEqual(len(results), 2)

    def test_categories_list(self):
        lib = self._lib()
        cats = lib.categories()
        self.assertEqual(cats, ["Connector", "Wire"])

    def test_manufacturers_list(self):
        lib = self._lib()
        mfrs = lib.manufacturers()
        self.assertIn("Molex", mfrs)
        self.assertIn("TE Connectivity", mfrs)


class TestLibraryFavorites(unittest.TestCase):
    def test_set_favorite(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="A"))
        self.assertTrue(lib.set_favorite("C1", True))
        self.assertTrue(lib.get_entry("C1").favorite)

    def test_favorites_list(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="A", favorite=True))
        lib.add_entry(LibraryEntry(entry_id="C2", category="Connector", name="B", favorite=False))
        favs = lib.favorites()
        self.assertEqual(len(favs), 1)

    def test_set_favorite_nonexistent(self):
        lib = ComponentLibrary()
        self.assertFalse(lib.set_favorite("NONEXIST", True))


class TestLibraryRecentlyUsed(unittest.TestCase):
    def test_mark_used(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="A"))
        lib.add_entry(LibraryEntry(entry_id="C2", category="Connector", name="B"))
        lib.mark_used("C1")
        lib.mark_used("C2")
        recent = lib.recently_used()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0].entry_id, "C2")  # Most recent first

    def test_mark_used_deduplicates(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(entry_id="C1", category="Connector", name="A"))
        lib.mark_used("C1")
        lib.mark_used("C1")
        lib.mark_used("C1")
        self.assertEqual(len(lib.recently_used()), 1)


class TestGenericToSpecific(unittest.TestCase):
    def test_set_specific_part(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="G1", category="Connector", name="Generic 2-Pin", is_generic=True,
        ))
        lib.add_entry(LibraryEntry(
            entry_id="S1", category="Connector", name="Molex 2-Pin",
            is_generic=False, manufacturer="Molex",
        ))
        self.assertTrue(lib.set_specific_part("G1", "S1"))
        resolved = lib.resolve_specific("G1")
        self.assertEqual(resolved.entry_id, "S1")

    def test_resolve_without_specific(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="G1", category="Connector", name="Generic", is_generic=True,
        ))
        resolved = lib.resolve_specific("G1")
        self.assertEqual(resolved.entry_id, "G1")

    def test_resolve_nonexistent_raises(self):
        lib = ComponentLibrary()
        with self.assertRaises(KeyError):
            lib.resolve_specific("NONEXIST")


class TestLibraryImportExport(unittest.TestCase):
    def test_csv_import(self):
        lib = ComponentLibrary()
        csv_data = (
            "entry_id,category,name,manufacturer,part_number,description,is_generic,favorite,certification_tier\n"
            "C1,Connector,2-Pin,Molex,123,,true,false,basic\n"
            "C2,Connector,4-Pin,TE,456,,false,true,certified\n"
        )
        count = lib.import_csv(csv_data)
        self.assertEqual(count, 2)
        self.assertEqual(lib.size, 2)
        c2 = lib.get_entry("C2")
        self.assertFalse(c2.is_generic)
        self.assertTrue(c2.favorite)
        self.assertEqual(c2.certification_tier, "certified")

    def test_csv_import_extra_columns(self):
        lib = ComponentLibrary()
        csv_data = (
            "entry_id,category,name,pin_count,voltage_rating\n"
            "C1,Connector,2-Pin,2,48V\n"
        )
        lib.import_csv(csv_data)
        entry = lib.get_entry("C1")
        self.assertEqual(entry.attributes["pin_count"], "2")
        self.assertEqual(entry.attributes["voltage_rating"], "48V")

    def test_csv_export(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="C1", category="Connector", name="2-Pin",
            manufacturer="Molex",
        ))
        csv_out = lib.export_csv()
        self.assertIn("entry_id", csv_out)
        self.assertIn("Molex", csv_out)

    def test_json_roundtrip(self):
        lib = ComponentLibrary()
        lib.add_entry(LibraryEntry(
            entry_id="C1", category="Connector", name="2-Pin",
            manufacturer="Molex", favorite=True,
            attributes={"pin_count": "2"},
        ))
        json_out = lib.to_json()
        lib2 = ComponentLibrary()
        count = lib2.from_json(json_out)
        self.assertEqual(count, 1)
        self.assertEqual(lib2.get_entry("C1").manufacturer, "Molex")
        self.assertEqual(lib2.get_entry("C1").attributes["pin_count"], "2")


class TestStarterLibrary(unittest.TestCase):
    def test_starter_has_connectors(self):
        lib = ComponentLibrary.create_starter_library()
        connectors = lib.search(category="Connector")
        self.assertGreaterEqual(len(connectors), 10)

    def test_starter_has_wires(self):
        lib = ComponentLibrary.create_starter_library()
        wires = lib.search(category="Wire")
        self.assertGreaterEqual(len(wires), 50)

    def test_starter_has_coverings(self):
        lib = ComponentLibrary.create_starter_library()
        coverings = lib.search(category="Covering")
        self.assertGreaterEqual(len(coverings), 4)

    def test_starter_has_clips(self):
        lib = ComponentLibrary.create_starter_library()
        clips = lib.search(category="Clip")
        self.assertGreaterEqual(len(clips), 4)

    def test_starter_has_splices(self):
        lib = ComponentLibrary.create_starter_library()
        splices = lib.search(category="Splice")
        self.assertGreaterEqual(len(splices), 4)

    def test_starter_favorites(self):
        lib = ComponentLibrary.create_starter_library()
        favs = lib.favorites()
        self.assertGreater(len(favs), 0)


if __name__ == "__main__":
    unittest.main()
