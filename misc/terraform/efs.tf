resource "aws_efs_file_system" "shared_efs" {
  creation_token = "capstone-efs"
  encrypted      = true
  tags           = { Name = "capstone-efs" }
}

# Mount targets in each app subnet
resource "aws_efs_mount_target" "mt" {
  for_each        = aws_subnet.app
  file_system_id  = aws_efs_file_system.shared_efs.id
  subnet_id       = each.value.id
  security_groups = [aws_security_group.efs.id]
}