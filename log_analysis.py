import os
import platform
import time
import re
import chardet
import tempfile
import zipfile
import shutil

class LogFile(object):
    name = ''
    path = ''
    file_create_time = 0.0

    __create_time_str = ""
    __uid_str = ""

    def __init__(self, path):
        self.path = path
        __, self.name = os.path.split(path)

    @property
    def create_time(self):
        if (len(self.__create_time_str) == 0) and (len(self.path) > 0):
            # self.file_create_time = os.path.getctime(self.path)
            # l_time = time.localtime(self.file_create_time)
            # self.__create_time_str = time.strftime('%Y-%m-%d %H:%M:%S', l_time)
            m = re.match(".*?([0-9]+_[0-9]+_[0-9]+)\.log.*", self.path)
            if not (m is None):
                self.__create_time_str = m.group(1).replace('_', '-')
            else:
                print("can't find createtime : ", self.name)
                file_create_time = os.path.getctime(self.path)
                l_time = time.localtime(file_create_time)
                self.__create_time_str = time.strftime('%Y-%m-%d', l_time)

        return self.__create_time_str

    @property
    def uid(self):
        if (len(self.__uid_str) == 0) and (len(self.path) > 0):
            m = re.match(".*?_(.*?)_.*", self.path)
            if not (m is None):
                self.__uid_str = m.group(1)
            else:
                print("can't find uid file name is : ", self.name)
                self.__uid_str = u"unkonwn"
        return self.__uid_str


class LogAnalysis(object):
    log_path = ""
    uid = 0
    files = []
    ctime_dict = {}

    def __init__(self, uid=0):
        sys_str = platform.system()
        self.uid = uid
        if sys_str == "Windows":
            self.log_path = os.path.join(os.getenv("appdata"), "com.futunn.FutuOpenD\\Log")
        else:
            pass #TODO 其他操作系统需要别的方式获取路径

    def __new__(cls):
        # 关键在于这，每一次实例化的时候，我们都只会返回这同一个instance对象
        if not hasattr(cls, 'instance'):
            cls.instance = super(LogAnalysis, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def load_file_list(log_path):
        f_list = []
        if len(log_path) > 0:
            ls = os.listdir(log_path)
            for f in ls:
                (filename, extension) = os.path.splitext(f)
                if extension == ".log" or extension == ".logs":
                    f_list.append(LogFile(os.path.join(log_path, f)))
        return f_list

    @staticmethod
    def safe_read_text(file_path):
        try:
            with open(file_path, 'rb') as fs:
                content = fs.read()
                #encoding = chardet.detect(content)['encoding']
                return content.decode("ascii")
        except:
            pass
        return None


    @staticmethod
    def read_dir(file_dir):
        content_dict = {}
        ls = os.listdir(file_dir)
        for f in ls:
            (_, extension) = os.path.splitext(f)
            file_full_path = os.path.join(file_dir, f)
            if extension != ".log":
                continue
            content = LogAnalysis.safe_read_text(file_full_path)
            if content is not None:
                content_dict[f] = content
        return content_dict


    @staticmethod
    def read_file(file_path):
        (_, extension) = os.path.splitext(file_path)
        if extension == ".logs":
            tmpfd = tempfile.mkdtemp(prefix='futu_opend')
            z = zipfile.ZipFile(file_path, 'r')
            z.extractall(path=tmpfd) #解压文件
            r = LogAnalysis.read_dir(tmpfd)
            shutil.rmtree(tmpfd)  # 删除文件夹
            return r
        elif extension == ".log":
            (_, filename) = os.path.split(file_path);
            content = LogAnalysis.safe_read_text(file_path)
            return {filename: content}

    @staticmethod
    def zip_dir(dirname, zipfilename):
        filelist = []
        if os.path.isfile(dirname):
            filelist.append(dirname)
        else:
            for root, dirs, files in os.walk(dirname):
                for dir in dirs:
                    filelist.append(os.path.join(root, dir))
                for name in files:
                    filelist.append(os.path.join(root, name))

        zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
        for tar in filelist:
            arcname = tar[len(dirname):]
            # print arcname
            zf.write(tar, arcname)
        zf.close()

    def load_ctime_dict(self):
        self.files = LogAnalysis.load_file_list(self.log_path)
        set_ctime = set()
        for f in self.files:
            set_ctime.add(f.create_time)
        #对时间进行排序
        list_ctime = list(set_ctime)
        list_ctime.sort(reverse=True)
        dict_list = []
        for ctime in list_ctime:
            dict_list.append({"ctime": ctime})
        return dict_list

    def read_log_by_time(self, ctime):
        if ctime in self.ctime_dict:
            return self.ctime_dict[ctime]
        if len(self.files) == 0:
            self.files = self.load_file_list(self.log_path)
        content_dict = {}
        for f in self.files:
            if f.create_time == ctime:
                d = LogAnalysis.read_file(f.path)
                content_dict.update(d)
        if len(content_dict) != 0:
            self.ctime_dict.clear()
            self.ctime_dict[ctime] = content_dict
        return content_dict

    #重新压缩文件
    def zip_log_by_time(self, ctime, zip_path):
        if len(self.files) == 0:
            self.files = self.load_file_list(self.log_path)
        tmpfd = tempfile.mkdtemp(prefix='futu_opend')
        for f in self.files:
            if f.create_time == ctime:
                (_, extension) = os.path.splitext(f.path)
                if extension == ".logs":
                    z = zipfile.ZipFile(f.path, 'r')
                    z.extractall(path=tmpfd)  # 解压文件
                elif extension == ".log":
                    (_, filename) = os.path.split(f.path)
                    shutil.copy(f.path, os.path.join(tmpfd, filename))
        zpath = os.path.join(zip_path, str(ctime + ".zip"))
        LogAnalysis.zip_dir(tmpfd, zpath)
        return zpath

    def log_by_time_dict(self, ctime):
        content_dict = self.read_log_by_time(ctime)
        if len(content_dict) > 0:
            dict_list = []
            for k, v in content_dict.items():
                (filename, _) = os.path.splitext(str(k))
                dict_list.append({"name": filename, "content": str(v)})
        return dict_list




LogAnalysisMgr = LogAnalysis()

if __name__ == '__main__':
    d = LogAnalysisMgr.log_by_time_dict("2018-12-04")
    print(d)
    zip_path = os.path.join(os.path.abspath(os.getcwd()), "static")
    LogAnalysisMgr.zip_log_by_time("2018-10-25", zip_path)
    print(zip_path)

    # f = open('D:\\GTWLog_0_2018_10_25.logs', 'rb')
    # content = f.read()
    # encoding = chardet.detect(content)['encoding']
    # print(content.decode(encoding))


    # print(LogAnalysisMgr.read_file("GTWLog_0_2018_10_25.logs"))
