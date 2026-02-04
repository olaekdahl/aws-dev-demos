# IAM role to allow SSM + cloud-init logging
resource "aws_iam_role" "app_ec2_role" {
  name               = "app-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.app_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.app_ec2_role.name
}

locals {
  user_data = <<-EOF
              #!/bin/bash
              set -eux
              yum install -y amazon-efs-utils nginx
              systemctl enable nginx
              systemctl start nginx

              mkdir -p /var/www/html
              echo "${aws_efs_file_system.shared_efs.dns_name}:/ /var/www/html efs defaults,_netdev 0 0" >> /etc/fstab
              mount -a
              echo "<h1>It works! Served from EFS: $(date)</h1>" > /var/www/html/index.html
              sed -i 's|root /usr/share/nginx/html;|root /var/www/html;|' /etc/nginx/nginx.conf
              systemctl restart nginx
              EOF
}

resource "aws_launch_template" "app" {
  name_prefix   = "capstone-app-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  user_data     = base64encode(local.user_data)
  iam_instance_profile { name = aws_iam_instance_profile.app_profile.name }
  network_interfaces { security_groups = [aws_security_group.app.id] }
  tag_specifications {
    resource_type = "instance"
    tags          = { Role = "app" }
  }
}

resource "aws_autoscaling_group" "app" {
  name                      = "capstone-asg"
  desired_capacity          = var.app_desired_capacity
  min_size                  = var.app_min_size
  max_size                  = var.app_max_size
  vpc_zone_identifier       = [for s in aws_subnet.app : s.id]
  health_check_type         = "ELB"
  health_check_grace_period = 60

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]
  lifecycle {
    create_before_destroy = true
  }
}