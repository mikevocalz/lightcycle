/** Runtime/glTF world coordinates. glTF, Three.js and Viro all use +Y as up. */
export type Vec3 = { x: number; y: number; z: number }

export type TrailPoint = Vec3 & {
  timeMs: number
  /** Starts a new wall segment (respawn, teleport, round reset, etc.). */
  breakBefore?: boolean
}

export type LightRibbonOptions = {
  maxPoints?: number
  minDistance?: number
  teleportDistance?: number
}

/**
 * Renderer-independent history for a Light Cycle ribbon.
 *
 * The GLB only carries LC_FX_TrailOrigin. Runtime code samples that transform
 * and feeds this path; renderers are free to turn the samples into a wall,
 * collision strip, nav obstacle, replay path, or all four.
 */
export class LightRibbonPath {
  readonly maxPoints: number
  readonly minDistanceSq: number
  readonly teleportDistanceSq: number
  private readonly points_: TrailPoint[] = []

  constructor(options: LightRibbonOptions = {}) {
    this.maxPoints = options.maxPoints ?? 768
    const minDistance = options.minDistance ?? 0.045
    const teleportDistance = options.teleportDistance ?? 2.5
    this.minDistanceSq = minDistance * minDistance
    this.teleportDistanceSq = teleportDistance * teleportDistance
  }

  get points(): readonly TrailPoint[] {
    return this.points_
  }

  clear(): void {
    this.points_.length = 0
  }

  break(): void {
    const last = this.points_.at(-1)
    if (last) last.breakBefore = last.breakBefore ?? false
    this.points_.push({
      x: last?.x ?? 0,
      y: last?.y ?? 0,
      z: last?.z ?? 0,
      timeMs: last?.timeMs ?? 0,
      breakBefore: true,
    })
  }

  append(position: Vec3, timeMs: number, forceBreak = false): boolean {
    const last = this.points_.at(-1)
    let breakBefore = forceBreak
    if (last) {
      const dx = position.x - last.x
      const dy = position.y - last.y
      const dz = position.z - last.z
      const d2 = dx * dx + dy * dy + dz * dz
      if (d2 > this.teleportDistanceSq) breakBefore = true
      if (!breakBefore && d2 < this.minDistanceSq) return false
    }

    this.points_.push({ ...position, timeMs, breakBefore })
    if (this.points_.length > this.maxPoints) {
      this.points_.splice(0, this.points_.length - this.maxPoints)
      if (this.points_[0]) this.points_[0]!.breakBefore = true
    }
    return true
  }

  /**
   * Contiguous polyline segments, split at respawns/teleports. One-point
   * fragments are omitted because they cannot form a wall quad.
   */
  segments(): TrailPoint[][] {
    const out: TrailPoint[][] = []
    let current: TrailPoint[] = []
    for (const p of this.points_) {
      if (p.breakBefore && current.length) {
        if (current.length > 1) out.push(current)
        current = []
      }
      current.push(p)
    }
    if (current.length > 1) out.push(current)
    return out
  }
}
