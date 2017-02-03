import sys
import os
import logging
import argparse
import maya.cmds as cmds
import maya.standalone


def main(argv):
    parser = argparse.ArgumentParser(description='Get partnames for group.')
    parser.add_argument('-group', help='Group Name', required=True)
    parser.add_argument('-file', help='File Name', required=True)

    # initialize maya
    maya.standalone.initialize('Python')
    args = parser.parse_args()

    group = args.group
    filename = args.file

    cmds.file(filename, o=True, f=True)
    parts = cmds.listRelatives(group, ad=True, type='mesh')
    finalParts = []

    # Ignore any intermediate objects
    for part in parts:
        if not cmds.getAttr(part+'.intermediateObject'):
            finalParts.append(part)

    logging.info("GEO_PARTS: " + ','.join(finalParts))

    cmds.quit()
    os._exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])


