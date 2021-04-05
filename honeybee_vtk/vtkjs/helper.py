"""This module helps in embedding vtkjs data in Paraview Glance HTML.

This module is originally developed by Kitware and can be found at the following link.
https://github.com/Kitware/VTK/blob/master/Web/Python/vtkmodules/web/vtkjs_helper.py

"""

import base64
import json
import re
import os
import shutil
import sys
import zipfile
import pathlib

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except ModuleNotFoundError:
    compression = zipfile.ZIP_STORED


def convert_directory_to_zip_file(
    directory_path: str, remove: bool = True, extension='zip', move=True
        ) -> str:

    if os.path.isfile(directory_path):
        return

    zip_file_path = f'{directory_path}.{extension}'
    zf = zipfile.ZipFile(zip_file_path, mode='w')

    try:
        for dir_name, _, file_list in os.walk(directory_path):
            for fname in file_list:
                full_path = pathlib.Path(dir_name, fname)
                rel_path = full_path.relative_to(directory_path)
                zf.write(
                    full_path.as_posix(),
                    arcname=rel_path.as_posix(),
                    compress_type=compression
                )
    finally:
        zf.close()

    if remove:
        shutil.rmtree(directory_path)
    if move:
        return shutil.move(zip_file_path, directory_path)
    else:
        return zip_file_path


def add_data_to_viewer(data_path, src_html_path=None):
    template = pathlib.Path(
        pathlib.Path(__file__).parent, '../assets/ParaViewGlance.html'
    ).resolve().as_posix()
    src_html_path = src_html_path or template
    if not os.path.isfile(data_path):
        raise FileNotFoundError(f'Failed to find {data_path}')
    if not os.path.exists(src_html_path):
        raise FileNotFoundError(f'Failed to find source html file: {src_html_path}')

    dstDir = os.path.dirname(data_path)
    dstHtmlPath = os.path.join(dstDir, "%s.html" % os.path.basename(data_path)[:-6])

    # Extract data as base64
    with open(data_path, 'rb') as data:
        data_content = data.read()
        base64Content = base64.b64encode(data_content)
        base64Content = base64Content.decode().replace('\n', '')

    # Create new output file
    with open(src_html_path, mode="r", encoding="utf-8") as srcHtml:
        with open(dstHtmlPath, mode="w", encoding="utf-8") as dstHtml:
            for line in srcHtml:
                if "</body>" in line:
                    dstHtml.write("<script>\n")
                    dstHtml.write('var contentToLoad = "%s";\n\n' % base64Content)
                    dstHtml.write(
                        'Glance.importBase64Dataset("%s" , contentToLoad, glanceInstance.proxyManager);\n'
                        % os.path.basename(data_path)
                    )
                    dstHtml.write("glanceInstance.showApp();\n")
                    dstHtml.write("</script>\n")

                dstHtml.write(line)

    return dstHtmlPath


def zipAllTimeSteps(directory_path):
    if os.path.isfile(directory_path):
        return

    class UrlCounterDict(dict):
        Counter = 0

        def GetUrlName(self, name):
            if name not in self.keys():
                self[name] = str(objNameToUrls.Counter)
                self.Counter = self.Counter + 1
            return self[name]

    def InitIndex(sourcePath, destObj):
        with open(sourcePath, "r") as sourceFile:
            sourceData = sourceFile.read()
            sourceObj = json.loads(sourceData)
            for key in sourceObj:
                destObj[key] = sourceObj[key]
            # remove vtkHttpDataSetReader information
            for obj in destObj["scene"]:
                obj.pop(obj["type"])
                obj.pop("type")

    def getUrlToNameDictionary(indexObj):
        urls = {}
        for obj in indexObj["scene"]:
            urls[obj[obj["type"]]["url"]] = obj["name"]
        return urls

    def addDirectoryToZip(
        dir_name, zipobj, storedData, rootIdx, timeStep, objNameToUrls
    ):
        # Update root index.json file from index.json of this timestep
        with open(os.path.join(dir_name, "index.json"), "r") as currentIdxFile:
            currentIdx = json.loads(currentIdxFile.read())
            urlToName = getUrlToNameDictionary(currentIdx)
            rootTimeStepSection = rootIdx["animation"]["timeSteps"][timeStep]
            for key in currentIdx:
                if key == "scene" or key == "version":
                    continue
                rootTimeStepSection[key] = currentIdx[key]
            for obj in currentIdx["scene"]:
                objName = obj["name"]
                rootTimeStepSection[objName] = {}
                rootTimeStepSection[objName]["actor"] = obj["actor"]
                rootTimeStepSection[objName]["actorRotation"] = obj["actorRotation"]
                rootTimeStepSection[objName]["mapper"] = obj["mapper"]
                rootTimeStepSection[objName]["property"] = obj["property"]

        # For every object in the current timestep
        for folder in sorted(os.listdir(dir_name)):
            currentItem = os.path.join(dir_name, folder)
            if os.path.isdir(currentItem) is False:
                continue
            # Write all data array of the current timestep in the archive
            for filename in os.listdir(os.path.join(currentItem, "data")):
                full_path = os.path.join(currentItem, "data", filename)
                if os.path.isfile(full_path) and filename not in storedData:
                    storedData.add(filename)
                    rel_path = os.path.join("data", filename)
                    zipobj.write(full_path, arcname=rel_path, compress_type=compression)
            # Write the index.json containing pointers to these data arrays
            # while replacing every basepath as '../../data'
            objIndexFilePath = os.path.join(dir_name, folder, "index.json")
            with open(objIndexFilePath, "r") as objIndexFile:
                objIndexObjData = json.loads(objIndexFile.read())
            for elm in objIndexObjData.keys():
                try:
                    if "ref" in objIndexObjData[elm].keys():
                        objIndexObjData[elm]["ref"]["basepath"] = "../../data"
                    if "arrays" in objIndexObjData[elm].keys():
                        for array in objIndexObjData[elm]["arrays"]:
                            array["data"]["ref"]["basepath"] = "../../data"
                except AttributeError:
                    continue
            currentObjName = urlToName[folder]
            objIndexrel_path = os.path.join(
                objNameToUrls.GetUrlName(currentObjName), str(timeStep), "index.json"
            )
            zipobj.writestr(
                objIndexrel_path,
                json.dumps(objIndexObjData, indent=2),
                compress_type=compression,
            )

    zip_file_path = "%s.zip" % directory_path
    currentDirectory = os.path.abspath(os.path.join(directory_path, os.pardir))
    rootIndexPath = os.path.join(currentDirectory, "index.json")
    rootIndexFile = open(rootIndexPath, "r")
    rootIndexObj = json.loads(rootIndexFile.read())

    zf = zipfile.ZipFile(zip_file_path, mode="w")
    try:
        # We copy the scene from an index of a specific timestep to the root index
        # Scenes should all have the same objects so only do it for the first one
        isSceneInitialized = False
        # currentlyAddedData set stores hashes of every data we already added to the
        # vtkjs archive to prevent data duplication
        currentlyAddedData = set()
        # Regex that folders storing timestep data from paraview should follow
        reg = re.compile(r"^" + os.path.basename(directory_path) + r"\.[0-9]+$")
        # We assume an object will not be deleted from a timestep to another so we
        # create a generic index.json for each object
        genericIndexObj = {}
        genericIndexObj["series"] = []
        timeStep = 0
        for item in rootIndexObj["animation"]["timeSteps"]:
            genericIndexObj["series"].append({})
            genericIndexObj["series"][timeStep]["url"] = str(timeStep)
            genericIndexObj["series"][timeStep]["timeStep"] = float(item["time"])
            timeStep = timeStep + 1
        # Keep track of the url for every object
        objNameToUrls = UrlCounterDict()

        timeStep = 0
        # zip all timestep directories
        for folder in sorted(os.listdir(currentDirectory)):
            full_path = os.path.join(currentDirectory, folder)
            if os.path.isdir(full_path) and reg.match(folder):
                if not isSceneInitialized:
                    InitIndex(os.path.join(full_path, "index.json"), rootIndexObj)
                    isSceneInitialized = True
                addDirectoryToZip(
                    full_path,
                    zf,
                    currentlyAddedData,
                    rootIndexObj,
                    timeStep,
                    objNameToUrls,
                )
                shutil.rmtree(full_path)
                timeStep = timeStep + 1

        # Write every index.json holding time information for each object
        for name in objNameToUrls:
            zf.writestr(
                os.path.join(objNameToUrls[name], "index.json"),
                json.dumps(genericIndexObj, indent=2),
                compress_type=compression,
            )

        # Update root index.json urls and write it in the archive
        for obj in rootIndexObj["scene"]:
            obj["id"] = obj["name"]
            obj["type"] = "vtkHttpDataSetSeriesReader"
            obj["vtkHttpDataSetSeriesReader"] = {}
            obj["vtkHttpDataSetSeriesReader"]["url"] = objNameToUrls[obj["name"]]
        zf.writestr(
            "index.json", json.dumps(rootIndexObj, indent=2), compress_type=compression
        )
        os.remove(rootIndexPath)

    finally:
        zf.close()

    shutil.move(zip_file_path, directory_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            'Usage: python helper.py /path/to/directory.vtkjs '
            '[/path/to/ParaViewGlance.html]'
        )
    else:
        fileName = sys.argv[1]
        convert_directory_to_zip_file(fileName)

        if len(sys.argv) == 3:
            add_data_to_viewer(fileName, sys.argv[2])
