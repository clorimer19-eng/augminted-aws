provider "aws" {
  region = "ap-southeast-1"
}

resource "aws_sqs_queue" "jobs" {
  name                       = "augminted-jobs"
  visibility_timeout_seconds = 600
  message_retention_seconds  = 86400

  tags = {
    Name = "augminted-jobs"
  }
}

resource "aws_s3_bucket" "pipeline" {
  bucket = "augminted-pipeline-prod"
}

resource "aws_ecr_repository" "repo" {
  name = "augminted-runner"
}

resource "aws_security_group" "ec2_sg" {
  name        = "augminted-ec2-sg"
  description = "Security group for Augminted EC2"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ec2_role" {
  name = "augminted-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "augminted-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_iam_role_policy" "s3_pipeline_access" {
  name = "augminted-s3-pipeline-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::augminted-pipeline-prod"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::augminted-pipeline-prod/*"
      }
    ]
  })
}

resource "aws_instance" "worker" {
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  ami                    = "ami-0e0c536a83eeae7a0"
  instance_type          = "t3.large"
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  key_name               = "augminted-key"

  tags = {
    Name = "augminted-worker"
  }
}
resource "aws_iam_role_policy" "sqs_access" {
  name = "augminted-sqs-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.jobs.arn
      }
    ]
  })
}
