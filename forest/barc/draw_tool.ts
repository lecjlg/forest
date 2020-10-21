import {Keys} from "core/dom"
import {UIEvent, PanEvent, TapEvent, MoveEvent, KeyEvent} from "core/ui_events"
import * as p from "core/properties"
import {isArray} from "core/util/types"
import {MultiLine} from "models/glyphs/multi_line"
import {Patches} from "models/glyphs/patches"
import {Bezier} from "models/glyphs/bezier"
//import {Circle} from "models/glyphs/circle"
//import {Text} from "models/glyphs/text"
import {PolyTool, PolyToolView} from "models/tools/edit/poly_tool"
import {bk_tool_icon_poly_draw} from "styles/icons"
//import {patch_to_column} from "models/sources/column_data_source"

import {ColumnDataSource} from "models/sources/column_data_source"
//import {GlyphRenderer} from "models/renderers/glyph_renderer"

export interface HasPolyGlyph {
  glyph: MultiLine | Patches | Bezier
}

export class FrontDrawToolView extends PolyToolView {
  model: FrontDrawTool
  _drawing: boolean = false
  _initialized: boolean = false

  _tap(ev: TapEvent): void {
    if (this._drawing)
      this._draw(ev, 'add', true)
    else
      this._select_event(ev, this._select_mode(ev), this.model.renderers)
  }

  _draw(ev: UIEvent, mode: string, emit: boolean = false): void {
    const renderer = this.model.renderers[0]
    const point = this._map_drag(ev.sx, ev.sy, renderer)

    if (!this._initialized)
      this.activate() // Ensure that activate has been called

    if (point == null)
      return

    const [x, y] = this._snap_to_vertex(ev, ...point)

    const cds = renderer.data_source
    const glyph: any = renderer.glyph
    //is Beziér
    //const [xkey, ykey] = [glyph.x0.field, glyph.y0.field]
    const [xkey, ykey] = ['xs','ys']
    const [x0key, y0key] = [glyph.x0.field, glyph.y0.field]
    const [x1key, y1key] = [glyph.x1.field, glyph.y1.field]
    const [cx0key, cy0key] = [glyph.cx0.field, glyph.cy0.field]
    const [cx1key, cy1key] = [glyph.cx1.field, glyph.cy1.field]
    if (mode == 'new') {
      this._pop_glyphs(cds, this.model.num_objects)
      if (xkey) cds.get_array(xkey).push([x, x])
      if (ykey) cds.get_array(ykey).push([y, y])
      if (x0key) cds.get_array(x0key).push([])
      if (y0key) cds.get_array(y0key).push([])
      if (x1key) cds.get_array(x1key).push([])
      if (y1key) cds.get_array(y1key).push([])
      if (cx0key) cds.get_array(cx0key).push([])
      if (cy0key) cds.get_array(cy0key).push([])
      if (cx1key) cds.get_array(cx1key).push([])
      if (cy1key) cds.get_array(cy1key).push([])
      this._pad_empty_columns(cds, [xkey, ykey, x0key, y0key, x1key, y1key, cx0key, cy0key, cx1key, cy1key])
    } else if (mode == 'edit') {
      if (xkey) {
        const xs = cds.data[xkey][cds.data[xkey].length-1]
        xs[xs.length-1] = x
      }
      if (ykey) {
        const ys = cds.data[ykey][cds.data[ykey].length-1]
        ys[ys.length-1] = y
      }
    } else if (mode == 'add') {
     if(glyph.x1.field) //if Bezier
     {
      const xidx = cds.data[xkey].length-1
      let xs = cds.get_array<number[]>(xkey)[xidx]
      const nx = xs[xs.length-1]
      xs[xs.length-1] = x
      if (!isArray(xs)) {
        xs = Array.from(xs)
        cds.data[xkey][xidx] = xs
      }
      //get columns
      let x0 = cds.get_array(x0key)
      let cx0 = cds.get_array(cx0key)
      let cx1 = cds.get_array(cx1key)
      let x1 = cds.get_array(x1key)
      let y0 = cds.get_array(y0key)
      let cy0 = cds.get_array(cy0key)
      let cy1 = cds.get_array(cy1key)
      let y1 = cds.get_array(y1key)
      let angle = cds.get_array('angle')

      xs.push(nx)
      if (x0key) {
        //once there are 4 points, and every three afterwards
        if((xs.length-1) == 4 || (((xs.length-2) % 3) ==0 && (xs.length-1) > 3))
        {
            //push the first value to beziér origin (x0) and so on
            if(isArray(x0[xidx]))
            {
               //contains the empty padding array, replace it
               x0[xidx] =xs[(xs.length-1) -4]
            } else {
               //add an extra one
               x0.push(xs[(xs.length-1) -4])
            }
            //cds.data[x0key][xidx] = xs[(xs.length-1) -4]
            if(isArray(cx0[xidx]))
            {
               //contains the empty padding array, replace it
               cx0[xidx] =xs[(xs.length-1) -3]
            } else {
               //add an extra one
               cx0.push(xs[(xs.length-1) -3])
            }
            //cds.data[cx0key][xidx] = xs[(xs.length-1) -3]
            if(isArray(cx1[xidx]))
            {
               //contains the empty padding array, replace it
               cx1[xidx] =xs[(xs.length-1) -2]
            } else {
               //add an extra one
               cx1.push(xs[(xs.length-1) -2])
            }
            //cds.data[cx1key][xidx] = xs[(xs.length-1) -2]
            //push current y as x1
            if(isArray(x1[xidx]))
            {
               //contains the empty padding array, replace it
               x1[xidx] =xs[(xs.length-1) -1]
            } else {
               //add an extra one
               x1.push(xs[(xs.length-1) -1])
            }
            //cds.data[x0key][xidx] = xs[(xs.length-1) -4]
            //cds.data[cx0key][xidx] = xs[(xs.length-1) -3]
            //cds.data[cx1key][xidx] = xs[(xs.length-1) -2]
            //push current x as x1
            //cds.data[x1key][xidx] = xs[(xs.length-1) -1]
        } 
      }
      const yidx = cds.data[ykey].length-1
      let ys = cds.get_array<number[]>(ykey)[yidx]
      const ny = ys[ys.length-1]
      ys[ys.length-1] = y
      if (!isArray(ys)) {
        ys = Array.from(ys)
        cds.data[ykey][yidx] = ys
      }
      ys.push(ny) 
      if (y0key) {
        if((ys.length-1) ==4 || (((ys.length-2) % 3) ==0 && (ys.length-1) > 3))
        {
            //set the first value to beziér origin (y0) and so on
            if(isArray(y0[yidx]))
            {
               //contains the empty padding array, replace it
               y0[xidx] =ys[(ys.length-1) -4]
            } else {
               //add an extra one
               y0.push(ys[(ys.length-1) -4])
            }
            //cds.data[y0key][yidx] = ys[(ys.length-1) -4]
            if(isArray(cy0[yidx]))
            {
               //contains the empty padding array, replace it
               cy0[xidx] =ys[(ys.length-1) -3]
            } else {
               //add an extra one
               cy0.push(ys[(ys.length-1) -3])
            }
            //cds.data[cy0key][yidx] = ys[(ys.length-1) -3]
            if(isArray(cy1[yidx]))
            {
               //contains the empty padding array, replace it
               cy1[xidx] =ys[(ys.length-1) -2]
            } else {
               //add an extra one
               cy1.push(ys[(ys.length-1) -2])
            }
            //cds.data[cy1key][yidx] = ys[(ys.length-1) -2]
            //push current y as y1
            if(isArray(y1[yidx]))
            {
               //contains the empty padding array, replace it
               y1[xidx] =ys[(ys.length-1) -1]
            } else {
               //add an extra one
               y1.push(ys[(ys.length-1) -1])
            }
            //cds.data[y1key][yidx] = ys[(ys.length-1) -1]


            //add padding to columns as required (all must be the same length)
            let xs_a = cds.get_array(xkey)
            let ys_a = cds.get_array(ykey)
            const pad_to = Math.max(...[xs_a.length, ys_a.length, x0.length, y0.length, x1.length, y1.length, cx0.length, cy0.length, cx1.length, cy1.length])
            const  cols = [xs_a, ys_a, angle]
            cols.forEach(function(col) {
               while(col.length < pad_to)
               {  
                  col.unshift(Array([]));
               }
            })
            const test_ds = new ColumnDataSource({ data: { x: [1, 0.5, 2], y: [1, 0.5, 2] , angle: [0,0,0]}})
            const ts = this.model.renderers[2]
            /*const ts = new Text({
               x: {field: "xs"},
               y: {field: "ys"},
               text: "Q"
            })*/
            //console.log(this.parent.model)
            //this.parent.model.glyphs({ field: "xs" }, {field: "ys"}, {source: test_ds, text: "Q"});
            ts.data_source.data = test_ds.data
            //ts.glyph.x = {field: 'xs'}
            //ts.glyph.y = {field: 'ys'}
            console.log(ts)
        } 
      }
     }
     else
     {
      if (xkey) {
        const xidx = cds.data[xkey].length-1
        let xs = cds.get_array<number[]>(xkey)[xidx]
        const nx = xs[xs.length-1]
        xs[xs.length-1] = x
        if (!isArray(xs)) {
          xs = Array.from(xs)
          cds.data[xkey][xidx] = xs
        }
        xs.push(nx)
      }
      if (ykey) {
        const yidx = cds.data[ykey].length-1
        let ys = cds.get_array<number[]>(ykey)[yidx]
        const ny = ys[ys.length-1]
        ys[ys.length-1] = y
        if (!isArray(ys)) {
          ys = Array.from(ys)
          cds.data[ykey][yidx] = ys
        }
        ys.push(ny)
      }
     }
    }
    this._emit_cds_changes(cds, true, false, emit)
  }

  _show_vertices(): void {
    if (!this.model.active) { return }
    const xs: number[] = []
    const ys: number[] = []
    for (let i=0; i<this.model.renderers.length; i++) {
      const renderer = this.model.renderers[i]
      const cds = renderer.data_source
      const glyph: any = renderer.glyph
      const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
      if (xkey) {
        for (const array of cds.get_array(xkey))
          Array.prototype.push.apply(xs, array)
      }
      if (ykey) {
        for (const array of cds.get_array(ykey))
          Array.prototype.push.apply(ys, array)
      }
      if (this._drawing && (i == (this.model.renderers.length-1))) {
        // Skip currently drawn vertex
        xs.splice(xs.length-1, 1)
        ys.splice(ys.length-1, 1)
      }
    }
    this._set_vertices(xs, ys)
  }

  _doubletap(ev: TapEvent): void {
    if (!this.model.active)
      return
    if (this._drawing) {
      this._drawing = false
      this._draw(ev, 'edit', true)
    } else {
      this._drawing = true
      this._draw(ev, 'new', true)
    }
  }

  _move(ev: MoveEvent): void {
    if (this._drawing) {
      this._draw(ev, 'edit')
    }
  }

  _remove(): void {
    const renderer = this.model.renderers[0]
    const cds = renderer.data_source
    const glyph: any = renderer.glyph
    const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
    if (xkey) {
      const xidx = cds.data[xkey].length-1
      const xs = cds.get_array<number[]>(xkey)[xidx]
      xs.splice(xs.length-1, 1)
    }
    if (ykey) {
      const yidx = cds.data[ykey].length-1
      const ys = cds.get_array<number[]>(ykey)[yidx]
      ys.splice(ys.length-1, 1)
    }
    this._emit_cds_changes(cds)
  }

  _keyup(ev: KeyEvent): void {
    if (!this.model.active || !this._mouse_in_frame)
      return
    for (const renderer of this.model.renderers) {
      if (ev.keyCode === Keys.Backspace) {
        this._delete_selected(renderer)
      } else if (ev.keyCode == Keys.Esc) {
        if (this._drawing) {
          this._remove()
          this._drawing = false
        }
        renderer.data_source.selection_manager.clear()
      }
    }
  }

  _pan_start(ev: PanEvent): void {
    if (!this.model.drag)
      return
    this._select_event(ev, "append", this.model.renderers)
    this._basepoint = [ev.sx, ev.sy]
  }

  _pan(ev: PanEvent): void {
    if (this._basepoint == null || !this.model.drag)
      return
    const [bx, by] = this._basepoint
    // Process polygon/line dragging
    for (const renderer of this.model.renderers) {
      const basepoint = this._map_drag(bx, by, renderer)
      const point = this._map_drag(ev.sx, ev.sy, renderer)
      if (point == null || basepoint == null)
        continue

      const cds = renderer.data_source
      // Type once dataspecs are typed
      const glyph: any = renderer.glyph
      const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
      if (!xkey && !ykey)
        continue
      const [x, y] = point
      const [px, py] = basepoint
      const [dx, dy] = [x-px, y-py]
      for (const index of cds.selected.indices) {
        let length, xs, ys
        if (xkey) xs = cds.data[xkey][index]
        if (ykey) {
          ys = cds.data[ykey][index]
          length = ys.length
        } else {
          length = xs.length
        }
        for (let i = 0; i < length; i++) {
          if (xs) xs[i] += dx
          if (ys) ys[i] += dy
        }
      }
      cds.change.emit()
    }
    this._basepoint = [ev.sx, ev.sy]
  }

  _pan_end(ev: PanEvent): void {
    if (!this.model.drag)
      return
    this._pan(ev)
    for (const renderer of this.model.renderers)
      this._emit_cds_changes(renderer.data_source)
    this._basepoint = null
  }

  activate(): void {
    if (!this.model.vertex_renderer || !this.model.active)
      return
    this._show_vertices()
    if (!this._initialized) {
      for (const renderer of this.model.renderers) {
        const cds = renderer.data_source
        cds.connect(cds.properties.data.change, () => this._show_vertices())
      }
    }
    this._initialized = true
  }

  deactivate(): void {
    if (this._drawing) {
      this._remove()
      this._drawing = false
    }
    if (this.model.vertex_renderer)
      this._hide_vertices()
  }
}

export namespace FrontDrawTool {
  export type Attrs = p.AttrsOf<Props>

  export type Props = PolyTool.Props & {
    drag: p.Property<boolean>
    num_objects: p.Property<number>
  }
}

export interface FrontDrawTool extends FrontDrawTool.Attrs {}

export class FrontDrawTool extends PolyTool {
  properties: FrontDrawTool.Props
  __view_type__: FrontDrawToolView

  constructor(attrs?: Partial<FrontDrawTool.Attrs>) {
    super(attrs)
  }

  static init_FrontDrawTool(): void {
    this.prototype.default_view = FrontDrawToolView

  }

  tool_name = "Polygon Draw Tool"
  icon = bk_tool_icon_poly_draw
  event_type = ["pan" as "pan", "tap" as "tap", "move" as "move"]
  default_order = 3
}

