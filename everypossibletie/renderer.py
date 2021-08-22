import os


def color_in(subset):
    from state_sets import safe_gop, safe_dem, STATES

    output = []
    for state in STATES:
        if state in safe_gop:
            color = "#aa4444"
        elif state in safe_dem:
            color = "#4444aa"
        elif state in subset:
            color = "#2222ff"
        else:
            color = "#ff2222"
        output.append(f".{state.replace('-', '').lower()} {{fill:{color}}}")
    return "\n".join(output)


def render_all_subsets(subsets, label):
    paths = []
    for i, subset in enumerate(subsets):
        with open("usa.svg") as f:
            svg = f.read()
        paths.append(f"temporary_outputs/{i}.svg")
        with open(paths[-1], "w") as f:
            f.write(
                svg.replace("/* REPLACE */", color_in(subset)).replace("$T", str(i + 1)).replace("Tie", label)
            )
    return paths


def stitch_together(paths, *, W, H, WH, HH, ncols, nrows, header_path, output_path):
    template = """
    <image
        preserveAspectRatio="none"
        inkscape:svg-dpi="400"
        width="{W}mm"
        height="{H}mm"
        xlink:href="{path}"
        id="image{i}"
        x="{x}mm"
        y="{y}mm" />
    """

    num_exclude = nrows * ncols - len(paths)
    assert num_exclude > 0
    exclude = []
    if num_exclude % 2 != ncols % 2:
        exclude.append((ncols // 2, nrows - 1))
        num_exclude -= 1
    pad_left = (ncols - num_exclude) // 2
    exclude += [(x, 0) for x in range(pad_left, pad_left + num_exclude)]

    assert HH == H
    assert WH <= WH * 2

    location_header = W * pad_left + num_exclude * W / 2 - WH / 2

    assert ncols * nrows - len(exclude) == len(paths)

    rendered = []
    paths_stack = paths[::-1]
    for col in range(ncols):
        for row in range(nrows):
            if (col, row) in exclude:
                continue
            rendered.append(
                template.format(
                    W=W,
                    H=H,
                    path=os.path.abspath(paths_stack.pop()),
                    x=col * W,
                    y=row * H,
                    i=len(paths_stack),
                )
            )
    rendered.append(
        template.format(
            W=WH,
            H=HH,
            path=os.path.abspath(header_path),
            x=location_header,
            y=0,
            i="header",
        )
    )
    with open("overall_template.svg", "r") as f:
        overall = f.read()
    overall = overall.replace("210", f"{W * ncols}")
    overall = overall.replace("297", f"{H * nrows}")
    with open(output_path, "w") as f:
        f.write(overall.replace("/* REPLACE */", "\n".join(rendered)))
    os.system(f'inkscape --export-type="png" {output_path} -w 4096')
