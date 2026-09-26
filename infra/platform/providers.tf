terraform {
  required_version = "= 1.15.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.61.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "= 4.4.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "= 3.2.1"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = module.standard_tags.tags
  }
}

provider "tls" {}

provider "kubernetes" {
  host                   = var.kubernetes_host
  token                  = var.kubernetes_token
  cluster_ca_certificate = base64decode(var.kubernetes_ca_certificate)
}
