provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "app" {
  name = "bedrock-reliability-lab-app"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "bedrock_invoke" {
  name        = "bedrock-reliability-lab-invoke"
  description = "Least-privilege starter policy for Bedrock inference."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "InvokeSelectedBedrockResource"
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = var.bedrock_model_resource_arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "bedrock" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.bedrock_invoke.arn
}

output "application_role_arn" {
  value = aws_iam_role.app.arn
}
