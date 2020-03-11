import urllib3
import boto3
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    eniinfo = ec2.NetworkInterface('eni-0b4ba5df3cec3def0').private_ip_address
    print(eniinfo)
    http = urllib3.PoolManager()
    print(http)
    #site = "10.99.70.195"
    urlvar = 'http://' + eniinfo
    try:
        r = http.request('GET', urlvar, headers={'Host': 'checkip.amazonaws.com'}, timeout=5.0, retries=1)
    except:
        print('*****path check failed*****')    
        return
    print(r)
    print(r.status)
    print(r.data)

    #if r.status == 200:
    if ('neverssl' in str(r.data)) and (r.status == 200):
        print('matched 200ok')
    else:
        print('FAILED')
        

