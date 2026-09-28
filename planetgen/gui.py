"""Desktop window for designing planets with a live preview.

Run with:  python -m planetgen.gui
"""

import os
import random
import threading
import tkinter as tk
from dataclasses import replace
from tkinter import filedialog, messagebox, ttk

from PIL import ImageTk

from .background import BACKGROUNDS
from .output import open_file, save_animation, save_planet
from .render import render_planet, render_spin
from .spec import PlanetSpec
from .types import PLANET_TYPES

PREVIEW_SIZE = 440
RANDOM = "Any type"

# (field, label, low, high, resolution)
SLIDERS = [
    ("light_azimuth", "Sun direction", 0, 360, 1),
    ("light_elevation", "Sun height", -80, 90, 1),
    ("tilt", "Axial tilt", -90, 90, 1),
    ("inclination", "Lean toward you", -60, 60, 1),
    ("rotation", "Turn", 0, 360, 1),
    ("clouds", "Clouds", 0, 1, 0.01),
    ("relief", "Terrain relief", 0, 3, 0.05),
    ("atmosphere_density", "Atmosphere", 0, 2.5, 0.05),
    ("hue", "Color shift", -180, 180, 1),
    ("scale", "Planet size", 0.1, 0.48, 0.005),
]


def _label(planet_type):
    return planet_type.replace("_", " ")


def _type_key(label):
    return label.replace(" ", "_")


class PlanetApp:
    def __init__(self, root):
        self.root = root
        self.spec = None
        self.preview_image = None
        self.render_serial = 0
        self.pending = None
        self.loading = False  # True while controls are filled from a spec

        root.title("Planet Generator")
        root.minsize(820, 560)
        self._build_controls()
        self._build_preview()
        self.new_planet(random.randint(0, 999_999))

    # ── Layout ──────────────────────────────────────────────────────────

    def _build_controls(self):
        panel = ttk.Frame(self.root, padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(panel, text="Planet type").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value=RANDOM)
        types = ttk.Combobox(panel, textvariable=self.type_var, state="readonly", width=18,
                             values=[RANDOM] + [_label(t) for t in sorted(PLANET_TYPES)])
        types.grid(row=0, column=1, columnspan=2, sticky="we", pady=2)
        types.bind("<<ComboboxSelected>>", lambda _: self.new_planet(self.spec.seed))

        ttk.Label(panel, text="Seed").grid(row=1, column=0, sticky="w")
        self.seed_var = tk.StringVar()
        seed_entry = ttk.Entry(panel, textvariable=self.seed_var, width=10)
        seed_entry.grid(row=1, column=1, sticky="we", pady=2)
        seed_entry.bind("<Return>", lambda _: self._seed_entered())
        ttk.Button(panel, text="New planet", command=self.randomize).grid(
            row=1, column=2, sticky="we", padx=(4, 0))

        ttk.Label(panel, text="Name").grid(row=2, column=0, sticky="w")
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(panel, textvariable=self.name_var)
        name_entry.grid(row=2, column=1, columnspan=2, sticky="we", pady=2)
        self.name_var.trace_add("write", lambda *_: self._set_field("name", self.name_var.get()))

        self.slider_vars = {}
        row = 3
        for field, label, low, high, step in SLIDERS:
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w")
            var = tk.DoubleVar()
            scale = tk.Scale(panel, variable=var, from_=low, to=high, resolution=step,
                             orient=tk.HORIZONTAL, length=190, showvalue=True,
                             command=lambda _v, f=field: self._slider_moved(f))
            scale.grid(row=row, column=1, columnspan=2, sticky="we")
            self.slider_vars[field] = var
            row += 1

        ttk.Label(panel, text="Moons").grid(row=row, column=0, sticky="w")
        self.moons_var = tk.IntVar()
        ttk.Spinbox(panel, from_=0, to=8, textvariable=self.moons_var, width=5).grid(
            row=row, column=1, sticky="w")
        self.moons_var.trace_add("write", lambda *_: self._moons_changed())
        row += 1

        self.flag_vars = {}
        for field, label in [("rings", "Rings"), ("cities", "City lights"),
                             ("show_moons", "Show moons")]:
            var = tk.BooleanVar()
            ttk.Checkbutton(panel, text=label, variable=var,
                            command=lambda f=field, v=var: self._set_field(f, v.get())).grid(
                row=row, column=0, columnspan=2, sticky="w")
            self.flag_vars[field] = var
            row += 1

        ttk.Label(panel, text="Background").grid(row=row, column=0, sticky="w")
        self.background_var = tk.StringVar(value="stars")
        backgrounds = ttk.Combobox(panel, textvariable=self.background_var, state="readonly",
                                   values=BACKGROUNDS, width=12)
        backgrounds.grid(row=row, column=1, sticky="w", pady=2)
        backgrounds.bind("<<ComboboxSelected>>", lambda _: self.schedule_render())
        row += 1

        ttk.Label(panel, text="Export size").grid(row=row, column=0, sticky="w")
        self.export_size_var = tk.IntVar(value=1024)
        ttk.Combobox(panel, textvariable=self.export_size_var, width=8,
                     values=[256, 512, 1024, 2048, 4096]).grid(row=row, column=1, sticky="w")
        row += 1

        buttons = ttk.Frame(panel)
        buttons.grid(row=row, column=0, columnspan=3, sticky="we", pady=(10, 0))
        ttk.Button(buttons, text="Save image", command=self.save_image).pack(fill=tk.X)
        ttk.Button(buttons, text="Save spinning animation",
                   command=self.save_spin).pack(fill=tk.X, pady=2)
        ttk.Button(buttons, text="Reset to rolled values",
                   command=lambda: self.new_planet(self.spec.seed)).pack(fill=tk.X)
        panel.columnconfigure(1, weight=1)

    def _build_preview(self):
        right = ttk.Frame(self.root, padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Label(right, background="#07080d")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.status_var = tk.StringVar()
        ttk.Label(right, textvariable=self.status_var, wraplength=PREVIEW_SIZE,
                  justify=tk.LEFT).pack(fill=tk.X, pady=(8, 0))

    # ── Planet state ────────────────────────────────────────────────────

    def new_planet(self, seed):
        """Roll a planet from a seed (keeping the chosen type) and show it."""
        chosen = self.type_var.get()
        self.spec = PlanetSpec.random(seed, type=None if chosen == RANDOM else _type_key(chosen))
        self._load_controls()
        self.schedule_render(delay=0)

    def randomize(self):
        self.new_planet(random.randint(0, 999_999))

    def _seed_entered(self):
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            self.status_var.set("The seed has to be a whole number.")
            return
        self.new_planet(seed)

    def _load_controls(self):
        self.loading = True
        try:
            self.seed_var.set(str(self.spec.seed))
            self.name_var.set(self.spec.name)
            for field, var in self.slider_vars.items():
                var.set(getattr(self.spec, field))
            self.moons_var.set(self.spec.moons)
            for field, var in self.flag_vars.items():
                var.set(getattr(self.spec, field))
        finally:
            self.loading = False

    def _moons_changed(self):
        try:
            count = int(self.moons_var.get())
        except (ValueError, tk.TclError):
            return  # half-typed number
        self._set_field("moons", max(0, min(count, 8)))

    def _slider_moved(self, field):
        self._set_field(field, float(self.slider_vars[field].get()))

    def _set_field(self, field, value):
        if self.loading or self.spec is None:
            return
        if getattr(self.spec, field) == value:
            return
        self.spec = replace(self.spec, **{field: value})
        # Name changes only affect the file name, not the picture.
        if field == "name":
            self._show_status()
        else:
            self.schedule_render()

    # ── Rendering ───────────────────────────────────────────────────────

    def schedule_render(self, delay=150):
        """Render after a short pause, so dragging a slider does not queue
        up a render for every step."""
        if self.pending is not None:
            self.root.after_cancel(self.pending)
        self.pending = self.root.after(delay, self._start_render)

    def _start_render(self):
        self.pending = None
        self.render_serial += 1
        serial = self.render_serial
        spec, background = self.spec, self.background_var.get()
        self.status_var.set("Rendering...")

        def work():
            try:
                image = render_planet(spec, PREVIEW_SIZE, background)
                error = None
            except Exception as exc:  # show it instead of dying silently
                image, error = None, exc
            self.root.after(0, lambda: self._render_done(serial, image, error))

        threading.Thread(target=work, daemon=True).start()

    def _render_done(self, serial, image, error):
        if serial != self.render_serial:
            return  # a newer render is on its way
        if error is not None:
            self.status_var.set(f"Could not render: {error}")
            return
        self.preview_image = ImageTk.PhotoImage(image)
        self.canvas.configure(image=self.preview_image)
        self._show_status()

    def _show_status(self):
        spec = self.spec
        self.status_var.set(
            f"{spec.name}. {spec.description}\n"
            f"{spec.temperature} °C, gravity {spec.gravity_g:.2f} g, "
            f"day {spec.day_length_hours} h, seed {spec.seed}"
        )

    # ── Saving ──────────────────────────────────────────────────────────

    def _export_size(self):
        try:
            size = int(self.export_size_var.get())
        except (ValueError, tk.TclError):
            size = 0
        if not 32 <= size <= 8192:
            messagebox.showerror("Export size", "Pick an export size between 32 and 8192.")
            return None
        return size

    def save_image(self):
        size = self._export_size()
        if size is None:
            return
        folder = filedialog.askdirectory(title="Save the planet into", initialdir="export",
                                         mustexist=False)
        if not folder:
            return
        spec, background = self.spec, self.background_var.get()
        self._run_in_background(
            "Saving...",
            lambda: save_planet(render_planet(spec, size, background), spec.to_dict(), folder),
            lambda paths: self._saved(paths[0]),
        )

    def save_spin(self):
        size = self._export_size()
        if size is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save the animation as", initialdir="export",
            initialfile=f"{self.spec.name}-spin.gif", defaultextension=".gif",
            filetypes=[("Animated GIF", "*.gif"), ("Animated WebP (keeps transparency)", "*.webp")],
        )
        if not path:
            return
        spec, background = self.spec, self.background_var.get()
        if path.lower().endswith(".gif") and background == "transparent":
            background = "black"
        # Animations get big fast; cap the frame size.
        frame_size = min(size, 512)

        def progress(done, total):
            self.root.after(0, lambda: self.status_var.set(
                f"Rendering animation: frame {done} of {total}"))

        self._run_in_background(
            "Rendering animation...",
            lambda: save_animation(render_spin(spec, frame_size, 36, background, progress), path),
            self._saved,
        )

    def _run_in_background(self, message, task, done):
        self.status_var.set(message)
        self.root.config(cursor="watch")

        def work():
            try:
                result, error = task(), None
            except Exception as exc:
                result, error = None, exc
            self.root.after(0, lambda: finish(result, error))

        def finish(result, error):
            self.root.config(cursor="")
            if error is not None:
                messagebox.showerror("Could not save", str(error))
                self._show_status()
            else:
                done(result)

        threading.Thread(target=work, daemon=True).start()

    def _saved(self, path):
        self._show_status()
        if messagebox.askyesno("Saved", f"Saved to {os.path.abspath(path)}\n\nOpen it now?"):
            open_file(path)


def main():
    root = tk.Tk()
    PlanetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
