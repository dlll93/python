#coding:utf8
import os,sys, getopt
import time
import random
import subprocess
import json
import re 
import ConfigParser  
from func_pycurl import funcCurl
reload(sys)
sys.setdefaultencoding( "utf-8" )

class hds_tools( ): 

    def __init__(self):
        self.err = open( "log/err.log", "a")
        pass
 
    def usage(self):
        print >> sys.stderr, "-u user name"	
        print >> sys.stderr, "-p password"
        print >> sys.stderr, "-o download data to local"
        print >> sys.stderr, "-s : check status of task[download/upload] ,     command is : -s -i task_id "	
        print >> sys.stderr, "-l : list %s\t"%self.list_type ," command is : -l project|datalist|data -i null|project_id|data_list_id"	
        print >> sys.stderr, '''-d : download label result with or without images, use -n with images 
\t1. -d  -i  data_list_id  [-n]                : download lastest version 
\t2. -d  -i  data_list_id  -v version [-n] 
\t3. -d  -i  data_list_id  -c class   [-n]     : download class in [%s] of lastest version 
\t4. -d  -r  task_id    -c class   [-n]        : download data in task(task_id),whatever doing or done'''
        print >> sys.stderr, "-a :  add label result of data_list_id as a new version, command is :  -a -i data_list_id -f file_path -m data_describe" 
    
    def confParser( self, argv ):
        self.list_type_value = None
        self.list_id = None
        self.task_id = None
        self.content = None
        self.data_version = None
        self.download_flag= None
        self.upload_flag= None
        self.status_flag= None
        self.file_path = None
        self.data_des= None
        self.need_image= False
        self.need_download = False

        self.conf = ConfigParser.ConfigParser() 
        self.conf.read("conf/hdf_tools.conf")  
        self.url = self.conf.get("api_common", "url")  
        self.version = self.conf.get("api_common", "version")  
        self.list_type = self.conf.get("list", "type").strip().split(",") 
 
        opts, args = getopt.getopt( argv[1:], "hadnsol:i:p:u:r:c:v:f:m:")
        ops = {}
        for op, value in opts:
            ops[op] = value
            if op == "-l":
                self.list_type_value = value
            elif op == "-i":
                if re.search(ur"^(\d+(#\d+)?,)*(\d+(#\d+)?)$", value):
                    self.list_id = value.split(",")
                else :
                    print >> sys.stderr, "data param %s is error" % value
                    sys.exit(0)
            elif op == "-r":
                self.task_id = value
            elif op == "-c":
                self.content = value 
            elif op == "-v":
                self.data_version = value 
            elif op == "-d":
                self.download_flag= True
            elif op == "-a":
                self.upload_flag = True
            elif op == "-s":
                self.status_flag= True
            elif op == "-f":
                self.file_path = value
            elif op == "-m":
                self.data_des = value
            elif op == "-n":
                self.need_image = "yes"
            elif op == "-o":
                self.need_download = True
            elif op == "-h":
                self.usage()
                sys.exit()

        if "-u" in ops.keys():
            self.user= ops['-u']
        else:
            self.user= self.conf.get("api_common", "user")
        if "-p" in ops.keys():
            self.password= ops['-p']
        else:
            print >> sys.stderr, "user is %s, use -p input password"%self.user
            sys.exit(0)

    def run(self): 
        data = {}
        data['version'] = self.version
        data['user'] = self.user
        data['user_password'] = self.password
        if not self.download_flag:
            if self.list_id is not None and len(self.list_id) == 1:
                self.list_id = self.list_id[0]

        if self.list_type_value in self.list_type :
            ret = self.list( data, self.list_type_value, self.list_id ) 
        elif self.status_flag and self.list_id:
            ret = self.status(data, self.list_id) 
        elif self.download_flag:
            ret = []
            if self.list_id is not None:
                for data_id in self.list_id:
                    raw = {}
                    data_info = data_id.split('#')
                    if len(data_info) == 2:
                        raw['version'] = data_info[1]
                    else :
                        raw['version'] = self.data_version

                    raw['data_id'] = data_info[0]
                    job_ret = self.download( data, raw['data_id'], None, self.content, raw['version'] )
                    #job_ret = self.getdata(raw['data_id'])
                    job_info = json.loads(job_ret)
                    task_id = self.extract_task_id(job_info['message'])
                    if task_id is not None:
                        raw['task_id'] = task_id
                        raw['ret'] = job_ret
                        ret.append(raw)
                        print >> sys.stderr, job_info['message']
                    else:
                        print >> sys.stderr, "data %s download error,ret is %s" % (raw['data_id'], job_ret)

            if self.list_id is None and self.task_id is not None:
                raw = {}
                raw['data_id'] = None
                job_ret = self.download(data, None, self.task_id, None, None)
                job_info = json.loads(job_ret)
                task_id = self.extract_task_id(job_info['message'])
                if task_id is not None:
                    raw['task'] = self.task_id
                    raw['task_id'] = task_id
                    raw['ret'] = job_ret
                    ret.append(raw)
                    print >> sys.stderr, job_info['message']
                else:
                    print >> sys.stderr, "task %s download error,ret is %s" % (raw['task'], job_ret)

            if self.need_download:
                flag = True
                while flag:
                    flag,left = self.downloadByTaskId(data, ret)
                    ret = left
                    if flag:
                        time.sleep(10)
            else:
                if len(ret) > 1:
                    print >> sys.stderr, json.dumps(ret)
                elif len(ret) == 1:
                    result = json.loads(ret[0]['ret'])
                    print >> sys.stderr, result['message']

            return True

        elif self.upload_flag and self.list_id and self.file_path and os.path.isfile( self.file_path) and self.data_des:
            ret = self.upload( data, self.list_id, self.file_path,self.data_des) 
        else:
            self.usage()
            sys.exit(-1)
        try:
            result = json.loads( ret)
            if result['status'] != 0:
                print >> sys.stderr,result['message']
                return False 
            else:
                self.var_dump( result['ret'], result['ret_format'] )
                return True
        except Exception as e:
            print >> sys.stderr, "[ERROR] encode json result error"
            print >> self.err.write( "\n[ERROR]\n%s\n%s"%(e,ret))
            return False 

    def chinese_str_len(self,str):  
        try:  
            row_l=len(str)
            utf8_l=len(str.decode('utf-8'))  
            return (row_l-utf8_l)/2 
        except:  
            return None  
        return None

    def var_dump( self, ret_json, ret_format):
        flag = True
        format_str = ""
        title_str = []
        count = 0
        for i in sorted( ret_format, key=lambda x:x[0]):
            format_str += "{0[%s]:<%s}|"%(count,i[2])
            title_str.append( i[1])
            count += 1
        print format_str.format( title_str)
        for i in ret_json:
            format_str = ""
            title_str = []
            count = 0
            for j in sorted( ret_format, key=lambda x:x[0]):
                lena =  self.chinese_str_len( str(i[j[1]]) )
                format_str += "{0[%s]:<%s}|"%(count ,j[2] - lena)
                if isinstance(i[j[1]], unicode):
                    #print >> sys.stderr,"debug",type(i[j[1]]),i[j[1]]
                    #title_str.append( i[j[1]].replace("\r\n",";;"))
                    tmp = re.sub( "\r\n|\r|\n|\t",";;",i[j[1]])
                    title_str.append( tmp) 
                else: 
                    title_str.append( i[j[1]])
                if re.search( "测试", str(i[j[1]])):
                    #print str(i[j[1]]),title_str,count
                    break
                count += 1
            if count == len( title_str):
                try:
                    print format_str.format( title_str)
                except Exception as e:
                    print >> self.err.write("\n[ERROR len] %s\n"%e+"\t".join([ str(t) for t in title_str])+"\n")

    def list( self, data,  key, value = None):
        op = funcCurl() 
        c = op.initCurl()
        data['type'] = "list" 
        data['list_type'] = key 
        data['list_type_value'] = value
        return op.PostData(c, self.url, data)
         
    def status( self, data, task_id):
        op = funcCurl() 
        c = op.initCurl()
        data['type'] = "status" 
        data['list_id'] = task_id
        return op.PostData(c, self.url, data)
         
    def download( self, data,  list_id, task_id, content, version):
        op = funcCurl() 
        c = op.initCurl()
        data['type'] = "download" 
        data['task_id'] = task_id
        data['data_id'] = list_id 
        data['contenttype'] = content 
        data['data_version'] = version 
        data['need_image'] = self.need_image 
        return op.PostData(c, self.url, data)
         
    def upload( self, data,list_id, file_path,data_des):
        op = funcCurl() 
        c = op.initCurl()
        data['type'] = "upload" 
        data['data_id'] = list_id 
        data['data_des'] = data_des 
        return op.PostFile(c, self.url, data, file_path)

    def downloadByTaskId(self, data, infos):
        flag = False
        left = []
        for task_info in infos:
            tmp = self.status(data, task_info['task_id'])
            #tmp = self.getstatus(task_info['task_id'])
            ret = json.loads(tmp)
            status_id,url = self.extract_task_url(ret['message'])
            if status_id == '0' :
                version = task_info['version']
                content_type = self.get_content_type(data, task_info['data_id'], version)
                if task_info['data_id'] is not None:
                    self.downloadToLocal(data, url, content_type, task_info['data_id'], version, 'data')
                elif task_info['task'] is not None:
                    self.downloadToLocal(data, url, content_type, task_info['task'], version, 'task')
                continue

            if status_id == '1' or status_id == '3' :
                left.append(task_info)
                flag = True
                continue

            print >> sys.stderr, "download error, ret is %s" % (ret['message'])

        return flag,left

    def downloadToLocal(self, data, url, content_type, type_id, version, type):
        dst_folder_name = "%s_%s_%s_v%s"%(type, type_id, content_type, version)

        download_file_name = url.split("\/")[-1]
        data_folder = download_file_name.split(".tar")[0]
        # rm if file or dir exist
        if os.path.exists(download_file_name):
            self.run_shell("rm ./%s" % (download_file_name))
        if os.path.exists(data_folder):
            self.run_shell("rm -r ./%s" % (data_folder))

        self.run_shell("wget %s" % (url))
        self.run_shell("tar -xf %s" % (download_file_name))
        self.run_shell("rm ./%s" % (download_file_name))
        if dst_folder_name is None:
            dst_folder_name = data_folder

        if dst_folder_name != data_folder:
            if os.path.exists(dst_folder_name):
                self.run_shell("mv %s/* %s" % (data_folder, dst_folder_name))
                self.run_shell("rm -r ./%s" % (data_folder))
            else:
                self.run_shell("mv %s %s" % (data_folder, dst_folder_name))
        return True

    def extract_task_url(self, msg):
        query_pattern = {
            # get task_id
            "-1": ur'task id (\d+) is not exist',
            # get download_url
            "0": ur'`s status is \u4e0b\u8f7d\u6570\u636e\u5b8c\u6210.{"code":0,"URL":"(.+)"}',
            # get waiting message
            "1": ur'(\u67e5\u627e\u6570\u636e\u5b8c\u6210,\u7b49\u5f85\u4e0b\u8f7d)',
            # get query data_id
            "2": ur'status is \u4e0d\u5b58\u5728data_id\u4e3a(\d+)',
            #wait for search data
            "3": ur'\u6b63\u5728\u67e5\u627e\u6570\u636e'}
        status_detail_id = None
        parse_result = None
        for k, v in query_pattern.items():
            result = re.findall(v, msg);
            if len(result) > 0:
                status_detail_id = k
                parse_result = result[0]

        return (status_detail_id, parse_result)

    def extract_task_id(self, str):
        status = re.findall(r'\[([A-Za-z]+)\]', str)
        if len(status) == 1 and status[0] == "Download":
            task_id = re.findall(r'\[(\d+)\]', str)
            return task_id[0]
        return None

    def get_content_type(self, data, data_id, version):
        tmp = self.list(data, 'data', data_id)
        if version is not None:
            version = int(version)
        ret = json.loads(tmp)
        for info in ret['ret']:
            if info['version'] == version:
                return info['content_type']

        return None


    def run_shell(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        p.wait()

    def getdata( self, data_id):
        if data_id == '463':
            id = '61119'

        if data_id == '514':
            id = '61126'
        str = '[Download]  output id is [%s],  message: 28, 50, 2,0' % id
        res = { 'status' : 1, 'message' : str}
        return json.dumps(res)

    def getstatus(self, task_id):
        if task_id == '61119':
            t = random.randint(0, 1)
            if t == 0:
                str = '[Status] 61119 `s status is 下载数据完成.{"code":0,"URL":"http:\/\/10.19.19.21\/output_dir\/61119\/datasystem_output_2016-11-28-16-40-06_976074.tar"}'
            else:
                str = 'status is (查找数据完成,等待下载)'

        if task_id == '61126':
            t = random.randint(0, 1)
            if t == 0:
                str = '[Status] 61126 `s status is 下载数据完成.{"code":0,"URL":"http:\/\/10.19.19.21\/output_dir\/61126\/datasystem_output_2016-11-28-17-10-50_100857.tar"}'
            else:
                str = 'status is (查找数据完成,等待下载)'

        res = {'status': 1, 'message': str}
        return json.dumps(res)

if __name__ == "__main__":
    op = hds_tools()
    op.confParser( sys.argv )
    op.run()
