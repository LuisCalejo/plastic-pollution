def install_packages(packages):
    print('test3')
    import sys
    import subprocess
    import os
    import bpy

    # Install packages into Blender:
    def python_exec():
        import os
        import bpy
        try:
            # 2.92 and older
            path = bpy.app.binary_path_python
        except AttributeError:
            # 2.93 and later
            import sys
            path = sys.executable
        return os.path.abspath(path)
    python_exe = python_exec()
    # upgrade pip
    subprocess.call([python_exe, "-m", "ensurepip"])
    subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    # install required packages
    for package in packages:
        print('installing '+package)
        subprocess.call([python_exe, "-m", "pip", "install", package])
