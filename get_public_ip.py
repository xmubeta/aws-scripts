#this is a Python 3 script
#this script is to collect all public IPs used within an AWS account.

import datetime
import time
import logging
import boto3
import sys
import traceback
#comment the following for python3


VERSION = 'v1.0'




max_retries = 10



logger = logging.getLogger(__name__)
logger.setLevel(level = logging.DEBUG)
handler = logging.FileHandler("get_all_ip.log")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)


def date_compare(snap):
    return snap["StartTime"] 

def setup_connection(client,profile_name):
    retry = 1
    while True:
        try:
            session = boto3.Session(profile_name=profile_name)
            conn = session.client(client)
    
            break
        except Exception as e:
            if "maximum" in str(e) or "RequestLimitExceeded" in str(e):
                if retry >= max_retries:
                    logger.error("Giving up boto3.client call.")
                    break
                logger.error("Hit the max API call limit for boto3.client" + ", sleep for " + str(retry) + " seconds and then retry.")
                logger.error(traceback.format_exc())
                time.sleep(retry) 
                retry += 1
            else:
                logger.error("Unexpected boto3.client error with details:" + str(e))
                logger.error(traceback.format_exc())
                break
                
    return conn






def get_all_public_ip(profile_name):
    try:
        ec2 = setup_connection('ec2',profile_name=profile_name)
        ni_list = []

        retry = 0
        marker = ''
        while True:
            try:
                if marker == '':
                    response_rp = ec2.describe_network_interfaces(MaxResults=1000)  
                else:
                    response_rp = ec2.describe_network_interfaces(
                        NextToken=marker,
                        MaxResults=1000)    

                if not response_rp:
                    break
                if 'NextToken' in response_rp:
                    marker = response_rp['NextToken']
                else:
                    marker = ''
                logger.info('current got resource: ' + str(len(response_rp['NetworkInterfaces'])))
                for ni in response_rp['NetworkInterfaces']:
                    if 'Association' in ni:
                        data = {}
                        data['PublicIp'] = ni['Association']['PublicIp']
                        
                        data['PrivateIpAddress'] = ni['PrivateIpAddress']
                        data['InterfaceType'] = ni['InterfaceType']
                        data['Description'] = ni['Description']
                        ni_list.append(data)
                if not response_rp['NetworkInterfaces'] or not marker:
                    logger.info('quit loop as no marker')
                    break
            
                    
            except Exception as e:
                if "maximum" in str(e) or "RequestLimitExceeded" in str(e):
                    if retry >= max_retries:
                        logger.error("Giving up boto3.client call.")
                        break
                    logger.error("Hit the max API call limit for boto3.client" + ", sleep for " + str(retry) + " seconds and then retry.")
                    time.sleep(retry) 
                    retry += 1
                else:
                    logger.error("Unexpected boto3.client error with details:" + str(e))
                    logger.error(traceback.format_exc())
                    break

                            
                    
                
        return ni_list
    except Exception as e:
        logger.error("Failed to get network interfaces" + str(e))
        logger.error(traceback.format_exc())

def help():
    print('Usage v1.0:')
    print('    get_all_ip.py <profile name>')
    print()
    print('    <profile name>:      Use <aws configure --profile profile_name> to configure')
    print()
    print('    If no profile name is specified, default is used')
    print()   

# Main
if __name__ == "__main__":
    print('Job is starting...' + VERSION)
    logger.info("Start.")
    if len(sys.argv) == 2 :
        profile_name = sys.argv[1]
    elif len(sys.argv) == 1:
        profile_name='default'
    else:
        help()
        exit(0)
    

    try:
        pip_list = get_all_public_ip(profile_name)
        logger.info('Loaded public ip list')

 
       

            
        todaydate = datetime.date.today()
        file_name =  'public-ip-'+ todaydate.strftime('%Y-%m-%d') +  '.csv'
        fw = open(file_name,'w')
        fw.write('PublicIp,PrivateIpAddress,InterfaceType,Description\n')
        
        for ip_item in pip_list:
            
            fw.write(ip_item['PublicIp'])
            fw.write(',')
            fw.write(ip_item['PrivateIpAddress'])
            fw.write(',')
            fw.write(ip_item['InterfaceType'])
            fw.write(',')
            fw.write(ip_item['Description'])
            fw.write('\n')
                
        fw.close()
        logger.info('Collecting Public IP is completed')

    except Exception as e:
        logger.error("Failed to collect network interfaces" + str(e))
        logger.error(traceback.format_exc())


    print('Job is done.')
    
