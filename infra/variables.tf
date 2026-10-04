variable "aws_region" {
  description = "AWS region for the lab."
  type        = string
  default     = "ap-southeast-2"
}

variable "bedrock_model_resource_arn" {
  description = "Exact Bedrock model/inference-profile resource ARN this workload may invoke."
  type        = string
}
