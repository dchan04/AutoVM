#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function # Python 2/3 compatibility
import boto3
import botocore
import paramiko
import csv
import time

#Azure stuff. Resource:https://docs.microsoft.com/en-us/azure/virtual-machines/windows/python
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute.models import DiskCreateOption
SUBSCRIPTION_ID = 'INSERT'
GROUP_NAME = 'vms'
LOCATION = 'canadacentral'
VNET_NAME = 'INSERT'
#VM_NAME = 'test-vm-01'
instanceCount = 0;
def get_credentials():
    credentials = ServicePrincipalCredentials(
        client_id = 'INSERT',
        secret = 'INSERT',
        tenant = 'INSERT'
    )
    return credentials

credentials = get_credentials()
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credentials, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credentials, SUBSCRIPTION_ID)

def create_vm(VM_NAME, publisher, offer, sku, vmSize, nicName, public_ipName):
	#subnet creation
	subnet = network_client.subnets.get(
		GROUP_NAME, VNET_NAME, 'default'
	)

	print("Creating public ip address for ", VM_NAME, "...")
	public_ip_addess_params = {
		'location': 'canadacentral',
		'public_ip_allocation_method': 'Dynamic'
    }
	public_creation = network_client.public_ip_addresses.create_or_update(
    	GROUP_NAME,
		public_ipName,
		public_ip_addess_params
	)
	public_creation.wait()
	print("<Done>")
	public_IPAddress = network_client.public_ip_addresses.get(
		GROUP_NAME, public_ipName
	)
	#network interface creation
	try:
		nic_params = {
			'location': 'canadacentral',
			'ip_configurations': [{
				'name': nicName,
				'public_ip_address': public_IPAddress,
				'subnet': {
					'id': subnet.id
				}
			}]
		}
	except Exception as ex:
		print(ex)
	print("Creating network interface for ", VM_NAME, "...")
	nic_create = network_client.network_interfaces.create_or_update(GROUP_NAME, nicName, nic_params)
	nic_create.wait()
	print("<Done>")
	nic = network_client.network_interfaces.get(
		GROUP_NAME, nicName
	)
	#VM creation
	print("Creating VM:", VM_NAME)
	VM_PARAMETERS={
		'location': 'canadacentral',
		'os_profile': {
		'computer_name': VM_NAME,
		'admin_username': 'INSERT',
		'admin_password': 'INSERT'
		},
		'hardware_profile': {
			'vm_size': vmSize
		},
		'storage_profile': {
			'image_reference': {
				'publisher': publisher,
				'offer': offer,
				'sku': sku,
				'version': 'latest'
			},
		},
		'network_profile': {
			'network_interfaces': [{
				'id': nic.id,
			}]
		},
    }
	vm_deploy = compute_client.virtual_machines.create_or_update(
		GROUP_NAME, VM_NAME, VM_PARAMETERS)
	print("Waiting for ", VM_NAME, " to finish Creating...")
	vm_deploy.wait()
	print("<", VM_NAME, "> successfully deployed\n")

#AWS stuff
ec2 = boto3.resource('ec2', 'ca-central-1')
ec2client = boto3.client('ec2', 'ca-central-1')

def show_instances(status):
    num = 0
    instances = ec2.instances.filter(
        Filters=[{'Name':'instance-state-name','Values':[status]}])
    if not instances:
        return num  # the list is empty
    for instance in instances:
        num = num + 1
        print(instance.id, instance.instance_type, instance.image_id, instance.state, 
              instance.public_dns_name)
    return num

# csv file name 
filename = "description.csv"
dockerFile = "docker.csv"
  
# initializing the titles and rows list 
fields = [] 
rows = []
dockFields = []
dockRows = []
  
# reading description file 
with open(filename, 'r') as csvfile: 
    csvreader = csv.reader(csvfile) 
    fields = csvreader.next() 
    for row in csvreader: 
        rows.append(row) 

# reading docker file
with open(dockerFile, 'r') as dockFile:
	dockreader = csv.reader(dockFile)
	dockFields = dockreader.next()
	for row in dockreader:
		dockRows.append(row)

#Creates the instances
for row in rows: 
    volSize = row[6]
    instaType = row[3].replace('-','.', 1)
    keyFile = row[7].strip('.pem')
    print("Creating Instance <", row[1],">...")
    if (row[0] == "AWS"):
    	if (row[5] == 'EBS'):
    		instances = ec2.create_instances(
    			BlockDeviceMappings=[
    				{
    					'DeviceName':'/dev/sdh',
    					'Ebs': {
    						'DeleteOnTermination': True,
    						'VolumeSize': int(volSize),
    						'VolumeType': 'gp2'
    					},
    				},
    			],
    			ImageId=row[2],
    			MinCount=1,
    			MaxCount=1,
    			InstanceType=instaType,
    			KeyName=keyFile,
    			SecurityGroupIds=[
    				'sg-0e06fd402ab67362a',
    			],
    			Monitoring={
    				'Enabled': True
    			},
    		)
    		print("Waiting until instance is running...")
        	instances[0].wait_until_running(
        		Filters=[
        			{
        				'Name': 'instance-id',
        				'Values': [
        					instances[0].instance_id,
        				]
        			},
        		],
        	)
    		resources = ec2.create_tags(
    			Resources=[
    				instances[0].instance_id,
    			],
    			Tags=[
    				{
    					'Key': row[0],
    					'Value': row[1]
    				},
    			]
    		)
    	else:
    		instances = ec2.create_instances(
    			ImageId=row[2],
    			MinCount=1,
    			MaxCount=1,
    			InstanceType=instaType,
    			KeyName=keyFile,
    			SecurityGroupIds=[
    				'sg-0e06fd402ab67362a',
    			],
    			Monitoring={
    				'Enabled': True
    			},
    		)
    		print("Waiting until instance is running...")
    		instances[0].wait_until_running(
        		Filters=[
        			{
        				'Name': 'instance-id',
        				'Values': [
        					instances[0].instance_id,
        				]
        			},
        		],
        	)
    		resources = ec2.create_tags(
    			Resources=[
    				instances[0].instance_id,
    			],
    			Tags=[
    				{
    					'Key': row[0],
    					'Value': row[1]
    				},
    			]
    		)
    	print("<",row[1],"> successfully created and running\n")
    elif (row[0] == "Azure"):
    	vmName = row[1]
    	imageName = row[2]
    	vmsSize = row[3]
    	if (imageName == "Ubuntu Server 16.04 LTS"):
    		print("Deploying: ", imageName)
    		pub = 'Canonical'
    		offer = 'UbuntuServer'
    		sku = '16.04.0-LTS'
    		nicName = "nic_" + str(instanceCount)
    		publicIP_name = "ip_"+vmName
    		instanceCount = instanceCount+1
    		try:
    			create_vm(vmName, pub, offer, sku, vmsSize, nicName, publicIP_name)
    		except Exception as ex:
    			print(ex)
    	elif (imageName == "Debian 10 \"Buster\""):
    		print("Deploying:", imageName)
    		pub = 'Debian'
    		offer = 'debian-10'
    		sku = '10'
    		nicName = "nic_" + str(instanceCount)
    		publicIP_name = "ip_"+vmName
    		instanceCount = instanceCount+1
    		try:
    			create_vm(vmName, pub, offer, sku, vmsSize, nicName, publicIP_name)
    		except Exception as ex:
    			print(ex)


#Loading Docker Images
for row in dockRows:
	if (row[0] == 'AWS'):
		response = ec2client.describe_instances(
			Filters=[
				{
					'Name': 'tag:'+row[0],
					'Values': [row[1]]
				}
			]
		)
		instancelist = []
		for reservation in (response["Reservations"]):
			for instance in reservation["Instances"]:
				instancelist.append(instance["InstanceId"])

		response2 = ec2client.describe_instances(
			InstanceIds=[
				instancelist[0],	
			],
		)
		for reservation in (response["Reservations"]):
			for instance in reservation["Instances"]:
				publicDNS = instance["PublicDnsName"]
				imageID = instance["ImageId"]
		pemkey = paramiko.RSAKey.from_private_key_file("cis4010-dchan04.pem")
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		print("Starting SSH into instance <", instancelist[0],">")
		commandList = []
		if (imageID == 'ami-00db12b46ef5ebc36' or imageID == 'ami-0fa94ecf2fef3420b'):
			print("error**")
			commandList = ['echo "Installing updates..."','sudo yum -y update', 'echo "Installing docker..."', 'sudo yum -y install docker.x86_64', 'sudo service docker start']
			dockerPull = 'sudo docker pull ' + row[2]
			command = 'echo "Pulling docker image <' + row[2] + '>"...'
			commandList.append(command)
			commandList.append(dockerPull)
			if (row[4] == 'N'):
				dockerRun = 'sudo docker run -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			elif (row[4] == 'Y'):
				dockerRun = 'sudo docker run -d -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			usrName = "ec2-user"
		elif (imageID == 'ami-0d0eaed20348a3389'):
			commandList = ['echo "Installing updates..."','sudo apt-get -y update', 'echo "Installing docker..."','sudo apt -y install docker.io']
			dockerPull = 'sudo docker pull ' + row[2]
			command = 'echo "Pulling docker image <' + row[2] + '>"...'
			commandList.append(command)
			commandList.append(dockerPull)
			if (row[4] == 'N'):
				dockerRun = 'sudo docker run -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			elif (row[4] == 'Y'):
				dockerRun = 'sudo docker run -d -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			usrName = "ubuntu"
		else:
			dockerPull = 'sudo docker pull ' + row[2]
			command = 'echo "Pulling docker image <' + row[2] + '>"...'
			commandList.append('sudo service docker start')
			commandList.append(command)
			commandList.append(dockerPull)
			if (row[4] == 'N'):
				dockerRun = 'sudo docker run -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				command.append('sudo service docker start')
				commandList.append(command)
				commandList.append(dockerRun)
			elif (row[4] == 'Y'):
				dockerRun = 'sudo docker run -d -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			usrName = "ec2-user"
		try:
			print(publicDNS)
			client.connect(hostname=publicDNS, username=usrName, pkey=pemkey)
			for command in commandList:
				stdin, stdout, stderr = client.exec_command(command)
				stdin.flush()
				data = stdout.read().splitlines()
				for line in data:
					print(line)
			client.close()
		except Exception as ex:
			print(ex)
		print("Ending current SSH connection\n")
	elif (row[0] == 'Azure'):
		ipName = 'ip_'+row[1]
		vmGet = compute_client.virtual_machines.get(GROUP_NAME, row[1])
		ipGet = network_client.public_ip_addresses.get(GROUP_NAME, ipName)
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		commandList = []
		if (vmGet.storage_profile.image_reference.publisher == 'Canonical'):
			commandList = ['echo "Installing docker..."','curl --fail --silent --show-error --location https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -', 'sudo apt-get install software-properties-common', 'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', 'sudo apt-get update']
			installCommand = 'echo \"INSERT\" | ' + 'sudo -S apt-get -y install docker-ce'
			commandList.append(installCommand)
			dockerPull = 'sudo docker pull ' + row[2]
			command = 'echo "Pulling docker image <' + row[2] + '>"...'
			commandList.append(command)
			commandList.append(dockerPull)
			if (row[4] == 'N'):
				dockerRun = 'sudo docker run -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			elif (row[4] == 'Y'):
				dockerRun = 'sudo docker run -d -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
		elif (vmGet.storage_profile.image_reference.publisher == 'Debian'):
			commandList = ['echo "Installing docker..."']
			installCommand = 'echo \"INSERT\" | ' + 'sudo -S apt -y install docker.io'
			commandList.append(installCommand)
			dockerPull = 'echo \"INSERT\" | ' + 'sudo -S docker pull ' + row[2]
			command = 'echo "Pulling docker image <' + row[2] + '>"...'
			commandList.append(command)
			commandList.append(dockerPull)
			if (row[4] == 'N'):
				dockerRun = 'echo \"INSERT\" | ' + 'sudo -S docker run -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
			elif (row[4] == 'Y'):
				dockerRun = 'echo \"INSERT\" | ' + 'sudo -S docker run -d -it --rm ' + row[2]
				command = 'echo "Running image <' + row[2] + '>"...'
				commandList.append(command)
				commandList.append(dockerRun)
		for command in commandList:
			client.connect(hostname=ipGet.ip_address, username='INSERT', password='INSERT')
			stdin, stdout, stderr = client.exec_command(command)
			stdin.flush()
			data = stdout.read().splitlines()
			for line in data:
				print(line)
			client.close()
