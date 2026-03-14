provider "aws" {
  region = "ap-southeast-1"
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

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "augminted-ec2-profile"
  role = aws_iam_role.ec2_role.name
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
