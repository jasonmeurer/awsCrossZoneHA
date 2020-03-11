# AWS Cross Zone Fault Tolerance


The intent of this project is to provide the necessary components to deploy a pair of Palo Alto Firewalls in 2 different zones of the same VPC.  The firewalls will then monitor each other and trigger a route table failover in the event the peer firewall is not passing traffic.  This solution overcomes the limitation of traditional HA being required to run within a given AZ.  This avoids the long CRON timer limitation when using CloudWatch events.

- The firewalls utilize Path Monitoring to determine if the peer firewall is passing traffic.
- The peer firewall destination NATs the ping probe on to 8.8.8.8.  (Configurable)
- The path monitor is not configured with a Preemptive Hold Timer ensure a rapid failover.
- In the event of a path outage, the firewall utilized Action Oriented Log Forwarding to notify an API Gateway of the outage.
- The firewall will pass the necessary VPC and ENI information to the API Gateway.
- The API Gateway triggers a Lambda Script to initiate the failover.
- The Lambda Script initiates a HTTP call to the firewall to validate the failover path is available.
- The firewall destination NATs the HTTP request on to http://checkip.amazonaws.com.
- If the path check is successful, the lambda searches all route tables in the VPC and replaces the down ENIs with the live ENI.
- No automated failback occurss.  Failback can be triggered from the desired firewall by hitting the "Send Test Log" button in the Payload Format dialog box in the HTTP Server profile.


{

  "vpcid": "vpc-xxxxxxxxxxx",
  
  "untrustdead": "eni-xxxxxxxxx",
  
  "untrustgood": "eni-xxxxxxxxxx",
  
  "trustdead": "eni-xxxxxxxxxxxx",
  
  "trustgood": "eni-xxxxxxxxxx"
  
}
