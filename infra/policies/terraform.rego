package main

required_tags := {"Project", "Environment", "Owner", "CostCenter", "ManagedBy", "LabId", "ExpiresAt"}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_db_instance"
  rc.change.after.publicly_accessible == true
  msg := sprintf("%s must not be publicly accessible", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_db_instance"
  rc.change.after.storage_encrypted != true
  msg := sprintf("%s must use storage encryption", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_elasticache_replication_group"
  rc.change.after.transit_encryption_enabled != true
  msg := sprintf("%s must use transit encryption", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_elasticache_replication_group"
  rc.change.after.at_rest_encryption_enabled != true
  msg := sprintf("%s must use at-rest encryption", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  startswith(rc.type, "aws_")
  missing := required_tags - object.keys(object.get(rc.change.after, "tags", {}))
  count(missing) > 0
  msg := sprintf("%s is missing required tags: %v", [rc.address, missing])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_security_group"
  rule := rc.change.after.ingress[_]
  rule.from_port <= 6379
  rule.to_port >= 5432
  rule.cidr_blocks[_] == "0.0.0.0/0"
  msg := sprintf("%s exposes data ports publicly", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_iam_role"
  contains(rc.change.after.assume_role_policy, "\"Principal\":\"*\"")
  msg := sprintf("%s has a wildcard IAM principal", [rc.address])
}

deny contains msg if {
  rc := input.resource_changes[_]
  rc.type == "aws_iam_role"
  contains(rc.change.after.assume_role_policy, "\"Federated\":\"*\"")
  msg := sprintf("%s has a wildcard federated principal", [rc.address])
}
