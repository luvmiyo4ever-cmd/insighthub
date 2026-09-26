{{- define "insighthub.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "insighthub.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "insighthub.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "insighthub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "insighthub.selectorLabels" -}}
app.kubernetes.io/name: {{ include "insighthub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "insighthub.webServiceAccountName" -}}
{{- if .Values.serviceAccounts.web.create }}{{ include "insighthub.fullname" . }}-web{{ else }}default{{ end }}
{{- end }}

{{- define "insighthub.apiServiceAccountName" -}}
{{- if .Values.serviceAccounts.api.create }}{{ include "insighthub.fullname" . }}-api{{ else }}default{{ end }}
{{- end }}

{{- define "insighthub.workerServiceAccountName" -}}
{{- if .Values.serviceAccounts.worker.create }}{{ include "insighthub.fullname" . }}-worker{{ else }}default{{ end }}
{{- end }}

{{- define "insighthub.runtimeEnv" -}}
- name: RAG_MODE
  value: {{ .Values.runtime.ragMode | quote }}
- name: LLM_PROVIDER
  value: {{ .Values.runtime.llmProvider | quote }}
- name: EMBEDDING_PROVIDER
  value: {{ .Values.runtime.embeddingProvider | quote }}
- name: LLM_MODEL
  value: {{ .Values.runtime.llmModel | quote }}
- name: EMBEDDING_MODEL
  value: {{ .Values.runtime.embeddingModel | quote }}
- name: EMBEDDING_DIM
  value: {{ .Values.runtime.embeddingDim | quote }}
- name: EMBEDDING_REVISION
  value: {{ .Values.runtime.embeddingRevision | quote }}
- name: LLM_MAX_TOKENS
  value: {{ .Values.runtime.llmMaxTokens | quote }}
- name: PROVIDER_TIMEOUT_SECONDS
  value: {{ .Values.runtime.providerTimeoutSeconds | quote }}
- name: CHUNK_SIZE
  value: {{ .Values.runtime.chunkSize | quote }}
- name: CHUNK_OVERLAP
  value: {{ .Values.runtime.chunkOverlap | quote }}
- name: RETRIEVAL_TOP_K
  value: {{ .Values.runtime.retrievalTopK | quote }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.runtime.databaseUrlSecret.name }}
      key: {{ .Values.runtime.databaseUrlSecret.key }}
- name: REDIS_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.runtime.redisUrlSecret.name }}
      key: {{ .Values.runtime.redisUrlSecret.key }}
{{- end }}
