variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type = string
}

variable "managed_by" {
  type    = string
  default = "terraform"
}

variable "lab_id" {
  type = string
}

variable "expires_at" {
  type = string
}
