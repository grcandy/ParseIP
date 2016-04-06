#coding:utf-8
import os
import glob
import argparse
import io


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument("fromfilesdir", help="""The file directoclearry to be merged, such as: /home/""")
    parser.add_argument("outputfile", help="The output destination of result, such as /home/ip_merge.txt")
    args = parser.parse_args()
    return args.fromfilesdir,args.outputfile

def joinFile(dir,outputfile):
    if not os.path.isdir(dir):
        print "不存在此目录"
        return False
    partfiles = glob.glob(os.path.join(dir,"*.txt"))
    partfiles.sort()

    # if os.path.isfile(outputfile):
    #     os.remove(outputfile)

    with io.open(outputfile,'a') as output:
        for txtFile in partfiles:
            with io.open(txtFile,'rb') as input:#系统会自动的采用缓冲IO和内存管理
                for line in input:
                    output.write(line)

def main():
    filedir,outputfile = init()
    joinFile(filedir,outputfile)


if __name__ == '__main__':
    main()

