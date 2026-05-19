locals {
  ingress_service_annotations = merge(
    {
      "service.beta.kubernetes.io/aws-load-balancer-type"             = "nlb"
      "service.beta.kubernetes.io/aws-load-balancer-scheme"           = "internet-facing"
      "service.beta.kubernetes.io/aws-load-balancer-backend-protocol" = "http"
      "service.beta.kubernetes.io/aws-load-balancer-attributes"       = "idle_timeout.timeout_seconds=120"
    },
    var.load_balancer_ssl_certificate_arn == null ? {} : {
      "service.beta.kubernetes.io/aws-load-balancer-ssl-cert"  = var.load_balancer_ssl_certificate_arn
      "service.beta.kubernetes.io/aws-load-balancer-ssl-ports" = "https"
    }
  )
}

resource "helm_release" "ingress" {
  name              = var.release_name
  namespace         = var.namespace
  chart             = "${path.module}/../../kube/apps/ingress"
  version           = var.chart_version
  create_namespace  = true
  dependency_update = true
  cleanup_on_fail   = true
  wait              = true
  timeout           = 600

  values = [
    file("${path.module}/../../kube/apps/ingress/values.yaml"),
    yamlencode({
      "ingress-nginx" = {
        controller = {
          service = {
            annotations = local.ingress_service_annotations
          }
        }
      }
      "oauth2-proxy" = {
        config = {
          clientID     = var.cognito_client_id
          clientSecret = var.cognito_client_secret
        }
        extraArgs = {
          "oidc-jwks-url"      = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}/.well-known/jwks.json"
          "oidc-issuer-url"    = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}"
          "redirect-url"       = "https://${var.oauth2_proxy_host}/oauth2/callback"
          "backend-logout-url" = "https://${var.oauth2_proxy_host}/oauth2/sign_out"
          "whitelist-domain"   = ".${var.root_domain},.amazoncognito.com"
          "cookie-domain"      = ".${var.root_domain}"
          "cookie-name"        = "_oauth2_proxy_${var.cognito_user_pool_domain}"
          "cookie-secret"      = var.oauth2_proxy_cookie_secret
        }
        ingress = {
          enabled = true
          hosts   = [var.oauth2_proxy_host]
          annotations = {
            "kubernetes.io/ingress.class"                      = "nginx"
            "nginx.ingress.kubernetes.io/proxy-buffer-size"    = "16k"
            "nginx.ingress.kubernetes.io/proxy-buffers-number" = "8"
          }
        }
      }
    })
  ]
}
