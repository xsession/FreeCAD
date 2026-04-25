import FreeCADGui as Gui
names = sorted(Gui.listWorkbenches().keys())
print('HAS_FLOWSTUDIO=' + str('FlowStudioWorkbench' in names))
print('FLOWSTUDIO_MATCHES=' + ','.join([n for n in names if 'Flow' in n or 'Studio' in n]))
