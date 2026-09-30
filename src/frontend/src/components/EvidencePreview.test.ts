import { describe, expect, it } from 'vitest'
import { getEvidencePreviewKind } from './EvidencePreview'

describe('getEvidencePreviewKind', () => {
  it('permite vista previa para imágenes', () => {
    expect(getEvidencePreviewKind('image/png')).toBe('image')
    expect(getEvidencePreviewKind('image/jpeg')).toBe('image')
  })

  it('permite vista previa para archivos PDF', () => {
    expect(getEvidencePreviewKind('application/pdf')).toBe('pdf')
  })

  it('mantiene otros formatos como solo descargables', () => {
    expect(getEvidencePreviewKind('application/octet-stream')).toBe('unsupported')
  })
})
