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

#Loading Docker Images
for row in rows:
	if (row[0] == 'AWS'):
		response = ec2client.describe_instances(
			Filters=[
				{
					'Name': 'tag:'+row[0],
					'Values': [row[1]]
				}
			]
		)
		#print(response)
		instancelist = []
		for reservation in (response["Reservations"]):
			for instance in reservation["Instances"]:
				instancelist.append(instance["InstanceId"])
	
		#print("Instance List:", instancelist)
		response2 = ec2client.describe_instances(
			InstanceIds=[
				instancelist[0],	
			],
		)
		for reservation in (response["Reservations"]):
			for instance in reservation["Instances"]:
				publicDNS = instance["PublicDnsName"]
				imageID = instance["ImageId"]
		#print(publicDNS)
		#print(imageID)
		pemkey = paramiko.RSAKey.from_private_key_file("cis4010-dchan04.pem")
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		print("\tVirtual Machine: <", row[1],">")
		commandList = ['echo "RUNNING IMAGES:"','sudo docker ps -a','echo "LIST OF IMAGES:"','sudo docker images']
		if (imageID == 'ami-0d0eaed20348a3389'):
			usrName = 'ubuntu'
		else:
			usrName = "ec2-user"
		try:
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
		print('\n')
	elif (row[0] == 'Azure'):
		ipName = 'ip_'+row[1]
		vmGet = compute_client.virtual_machines.get(GROUP_NAME, row[1])
		#print(vmGet.storage_profile.image_reference.publisher)
		#print(vmGet)
		ipGet = network_client.public_ip_addresses.get(GROUP_NAME, ipName)
		#print(ipGet.ip_address)
		#print(ipGet)
		#pemkey = paramiko.RSAKey.from_private_key_file("/Users/darrenchan/.ssh/id_rsa.pub")
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		commandList = []
		print("\tVirtual Machine: <", row[1],">")
		if (vmGet.storage_profile.image_reference.publisher == 'Debian'):
			commandList = ['echo "RUNNING IMAGES:"','echo \"INSERT\" | ' + 'sudo -S docker ps -a','echo "LIST OF IMAGES:"','echo \"INSERT\" | ' + 'sudo -S docker images']
		else:
			commandList = ['echo "RUNNING IMAGES:"','sudo docker ps -a','echo "LIST OF IMAGES:"','sudo docker images']
		for command in commandList:
			client.connect(hostname=ipGet.ip_address, username='INSERT', password='INSERT')
			stdin, stdout, stderr = client.exec_command(command)
			stdin.flush()
			data = stdout.read().splitlines()
			for line in data:
				print(line)
			client.close()
		print('\n')
