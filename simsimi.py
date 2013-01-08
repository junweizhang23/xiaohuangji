#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


# 从simsimi读数据

import requests
import cookielib
import MySQLdb
import random
import hashlib
import time
from settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DBNAME


rd = random.SystemRandom()


class SimSimi:

    def __init__(self):
        r = requests.get('http://www.simsimi.com/talk.htm')
        self.chat_cookies = r.cookies

        r = requests.get('http://www.simsimi.com/teach.htm')
        self.teach_cookies = r.cookies

        self.headers = {
            'Referer': 'http://www.simsimi.com/talk.htm'
        }

        self.chat_url = 'http://www.simsimi.com/func/req?lc=ch&msg=%s'
        self.teach_url = 'http://www.simsimi.com/func/teach'
        self.local_cache = {}

    def _int32_hashcode(self, message=''):
        return int(int(hashlib.md5(message).hexdigest(), 16) % (2 ** 30))

    def read_cache(self, message=''):
        if message:
            if message in self.local_cache and self.local_cache[message]:
                return rd.choice(self.local_cache[message])
            conn = None
            res = None
            try:
                conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASS,
                        db=MYSQL_DBNAME, charset="utf8", use_unicode=False)
                cursor = conn.cursor()
                sql = "SELECT * FROM simsimi_answers WHERE hashcode = %s AND question = %s AND creationtime >= %s"
                cursor.execute(sql, (self._int32_hashcode(message), message, int(time.time() - 3600 * 24)))
                l = cursor.fetchall()
                self.local_cache[message] = list(set([k[2] for k in l]))
                if l:
                    res = rd.choice(list(set(l)))[2]
            finally:
                if conn:
                    conn.close()
            return res
        else:
            return None

    def write_to_cache(self, message='', answer=''):
        if message and answer:
            conn = None
            try:
                conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASS,
                        db=MYSQL_DBNAME, charset="utf8", use_unicode=False)
                cursor = conn.cursor()

                #理论上来说需要事务，但实际环境中，不需要严格的事务，重复了就重复了呗。
                sql_search = "SELECT * FROM simsimi_answers WHERE hashcode = %s AND question = %s AND answer = %s"
                sql_insert = "INSERT INTO simsimi_answers (hashcode, question, answer, creationtime) VALUES(%s, %s, %s, %s)"
                sql_update = "UPDATE simsimi_answers SET creationtime = %s WHERE hashcode = %s AND question = %s AND answer = %s"
                cursor.execute(sql_search, (self._int32_hashcode(message), message, answer))
                if cursor.fetchone():
                    cursor.execute(sql_update, (int(time.time()), self._int32_hashcode(message), message, answer))
                else:
                    cursor.execute(sql_insert, (self._int32_hashcode(message), message, answer, int(time.time())))
            except Exception as e:
                print e
            finally:
                if conn:
                    conn.close()

    def chat(self, message=''):
        if message:
            if rd.choice([True, True, False]) and self.read_cache(message):
                return self.read_cache(message).decode('UTF-8')
            r = requests.get(self.chat_url % message, cookies=self.chat_cookies, headers=self.headers)
            self.chat_cookies = r.cookies
            try:
                answer = r.json()['response']
                self.write_to_cache(message, answer)
                return answer
            except:
                return u'呵呵'
        else:
            return u'叫我干嘛'

    def teach(self, req, resp):
        data = {
            'req': req,
            'resp': resp,
            'lc': 'ch',
            'snsinfo': '{"sid":"1432328384", "stype":"facebook", "sname":"王大鹏", "stoken":"AAAFRQIFUlkgBAPKP1DkWkDRuhGDpO2mZCbgq38t90ZC9U1VlstKQEH0OUt8sWUzdGBFWoGz4Wegbm0ZA4LyjaBQ6p0OIrZCg1nnp0JiiqPgjVWNwoGoh", "sshare":"off"}'
        }
        r = requests.post(self.teach_url, data, cookies=self.teach_cookies, headers=self.headers)
        print r.text


if __name__ == '__main__':
    simi = SimSimi()
    print simi.chat('最后一个问题')
    #simi.teach('一切的答案', '42')
