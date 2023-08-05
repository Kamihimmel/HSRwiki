import os
import oss2
from aliyunsdkcore.client import AcsClient
from aliyunsdkcdn.request.v20180510 import RefreshObjectCachesRequest

# OSS 配置
auth = oss2.Auth(os.getenv('OSS_ACCESS_KEY_ID'), os.getenv('OSS_ACCESS_KEY_SECRET'))
bucket = oss2.Bucket(auth, os.getenv('OSS_ENDPOINT'), os.getenv('OSS_BUCKET'))

# CDN 配置
client = AcsClient(os.getenv('CDN_ACCESS_KEY_ID'), os.getenv('CDN_ACCESS_KEY_SECRET'), 'cn-beijing')

# 本地文件目录路径
folder_path = '.'

# 遍历目录并上传文件到 OSS
for root, _, files in os.walk(folder_path):
    for file in files:
        local_file = os.path.join(root, file)
        oss_file = os.path.relpath(local_file, folder_path).replace('\\', '/')
        print(f'Uploading {local_file} to {oss_file}')  # 添加调试信息
        bucket.put_object_from_file(oss_file, local_file)


# 刷新 CDN 缓存
request = RefreshObjectCachesRequest.RefreshObjectCachesRequest()
request.set_accept_format('json')
# request.set_ObjectPath(f"https://{os.getenv('CDN_DOMAIN')}/")
request.set_ObjectPath('https://hsrwikidata.kchlu.com/')
response = client.do_action_with_exception(request)

print(str(response, encoding='utf-8'))
