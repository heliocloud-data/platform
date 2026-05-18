output "portal_subnet_id" {
  description = "ID of the subnet containing the ec2 instances spawned by the HelioCloud User Portal."
  value       = aws_subnet.HelioCloud_Portal_Subnet_Public_01.id
}

output "portal_identity_pool_id" {
  description = ""
  value       = aws_cognito_identity_pool.HelioCloud_Portal_IdentityPool.id
}

output "portal_ec2_instance_profile_arn" {
  description = ""
  value       = aws_iam_instance_profile.HelioCloud_Portal_UserInstanceProfile.arn
}

output "portal_security_group_id" {
  description = ""
  value       = aws_security_group.HelioCloud_Portal_UserSecurityGroup.id
}


output "portal_user_role_arn" {
  description = ""
  value       = aws_iam_role.HelioCloud_Portal_UserRole.arn
}
