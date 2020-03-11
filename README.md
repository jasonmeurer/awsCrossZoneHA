# AWS Cross Zone Fault Tolerance

## Overview
The intent of this project is to provide the necessary components to deploy a pair of Palo Alto Firewalls in 2 different zones of the same VPC.  The firewalls will then monitor each other and trigger a route table failover in the event the peer firewall is not passing traffic.  This solution overcomes the limitation of traditional HA being required to run within a given AZ.  This avoids the long CRON timer limitation when using CloudWatch events.

Common drivers for this solution are East-West routing in a [Transit Gateway Design](https://www.paloaltonetworks.com/resources/guides/aws-transit-gateway-deployment-guide) and [AWS Ingress Routing](https://live.paloaltonetworks.com/t5/Blogs/Amazon-Web-Services-AWS-Ingress-Routing/ba-p/300885).  The user can select from either the single NIC solution (_Still under deveolpment_) or the dual NIC solution.  Single NIC solutions will typically be utlized for single Zone design for example TGW East-West.  Dual NIC designs are typical in a two Zone for example Ingress Routing.

This solution assumes prior knowledge of AWS EC2, S3 and VPC constructs including Routing, Security Groups and EIPs.  It also assumes prior Palo Alto Networks NGFW knowledge including both the CLI and Web Console.

#### Solution Flow
- The CloudFormation will deploy the following.
  + AWS::ApiGateway::Deployment
  + AWS::ApiGateway::Method
  + AWS::ApiGateway::Resource
  + AWS::ApiGateway::RestApi
  + AWS::ApiGateway::Stage
  + AWS::EC2::Instance (2 instances each with 3 interfaces)
  + AWS::EC2::VPCEndpoint
  + AWS::IAM::Role
  + AWS::Lambda::Function
  + AWS::Lambda::Permission

- The firewalls utilize Path Monitoring to determine if the peer firewall is passing traffic.
  + The peer firewall destination NATs the ping probe on to 8.8.8.8.  (Configurable)
- The path monitor is not configured with a Preemptive Hold Timer ensure a rapid failover.
- In the event of a path outage, the firewall utilized Action Oriented Log Forwarding to notify an API Gateway of the outage.
- The firewall will pass the necessary VPC and ENI information to the API Gateway.
- The API Gateway triggers a Lambda Script to initiate the failover.
- The Lambda Script initiates a HTTP call to the firewall to validate the failover path is available.
  + The firewall destination NATs the HTTP request on to http://checkip.amazonaws.com. (Configurable)
- If the path check is successful, the lambda searches all route tables in the VPC and replaces the down ENIs with the live ENI.
- No automated failback occurss.  Failback can be triggered from the desired firewall by hitting the "Send Test Log" button in the Payload Format dialog box in the HTTP Server profile.

## CloudFormation Deployment
This solution is intended for retrofit into an existing VPC environment.  The following items are required to deploy the CloudFormation template.

#### Prequisites
Download the python file corresponding to you deployment model and add it to zip file.  Create an S3 bucket within region and upload the newly created zip.  Make note of both the bucket and zip file name for use in the CFT deployment.

Download the YAML file corresponding to your deployment model and launch a CloudFormation template utilizing it. 

- FW0MgmtSubnet
- FW0TrustSubnet
- FW0UntrustSubnet
- FW1MgmtSubnet
- FW1TrustSubnet
- FW1UntrustSubnet
- FWInstanceType
- [FirewallAMI](https://docs.paloaltonetworks.com/compatibility-matrix/vm-series-firewalls/aws-cft-amazon-machine-images-ami-list) 
- KeyName
- Security Group Assigned to API Gateway and Lambda endpoints
- Subnets for the API Gateway and Lamnda endpoints
- S3Bucket (Used to store the lambda function code contained in a zip file)
- S3Key (Name of the zip file)
- VPCID

#### CloudFormation Outputs
The following information is outputted by the CFT for subsequent use in the firewall configuration script.

- ApiGwUrl
- FW0TrustENI
- FW0UntrustENI
- FW1TrustENI
- FW1UntrustENI
- Fw0TrustIP
- Fw1TrustIP

## Firewall Configuration Deployment
This solution assume the existence of route tables and security groups in the VPC.  Once the firewalls are deployed, the following steps should be performed.

1. Apply Security Groups to all firewall interfaces to ensure necessary access.  
2. Apply EIPs where necessary.
    + If managing the firewall via the internet, apply an EIP to ETH0.
    + If the firewall will route traffic to or from an IGW, apply an EIP to ETH1.
3. Make note of the following items as they will utilized in the firewall configuration.
    + +++_ VPC_ID_+++
    + +++_ VPC_CIDR_+++
    + +++_ SECOND_IP_OF_VPC_CIDR_+++
    + +++_ YOUR_API_GATEWAY_HOST__+++
    + +++_ First_IP_of_Trust_subnet_+++
    + +++_ Lambda1_CIDR_+++
    + +++_ Lambda2_CIDR_+++
    + Fw Trust IPs
    + Fw ETH1 ETH2 ENIs
4. SSH into each of the firewalls to configure them with the CLI commands found in the [CLI Text File](https://raw.githubusercontent.com/jasonmeurer/awsCrossZoneHA/master/crosszonehafirewallconfig.txt)
5. Update the appropriate route tables to point to ENIs of "primary" firewall.

## Validation
In each of the firewalls, there will a periodic Ping from the peer firewall's trust IP to the local Trust interface that is allowed and NATed on to 8.8.8.  Failover can be triggered via the peer firewall by Sending a Test Log. 
1. Device Tab, Server Profiles, HTTP.  
2. Open the AWS_HA_Down object.
3. Payload Format tab.
4. Open the System Log Type.
5. Hit the "Send Test Log" button. 
6. A dialog will open with Test Results Successfully Sent.
Access the Monitor Tab of the firewall and verify that an HTTP request has been recieved from either of the Lambda endpoints and succesfully NATed to checkip.amazonaws.com.

Access CloudWatch in the AWS console.  Select Logs and then Log Groups.  Open the stream /aws/lambda/<function_name>.  You can now observe the output of the Path check along with which routes and route tables were modified.
