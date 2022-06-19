from downloader import reverse_geocode


def precinct_label(row):
    total = row.R + row.D + row.O
    margin = row.D - row.R
    margin = margin / total
    if margin < 0:
        return f'<div class="text gop_precinct">Precinct Margin: R+{-margin:.0%}</div>'
    else:
        return f'<div class="text dem_precinct">Precinct Margin: D+{margin:.0%}</div>'


def render_degree(val, dirs):
    direction = dirs[int(val > 0)]
    val = abs(val)
    degree = int(val)
    val -= degree
    val *= 60
    minutes = int(val)
    val -= minutes
    val *= 60
    seconds = int(val)
    return str(degree) + "&deg;" + str(minutes) + "'" + str(seconds) + '"' + direction


def render_coordinate(row):
    return render_degree(row.y, "SN") + " " + render_degree(row.x, "WE")


def render_voter(row, idx):
    if row.selected_party == "D":
        return f'<div class="text dem_voter">Voter {idx + 1} voted for Biden</div>'
    else:
        return f'<div class="text gop_voter">Voter {idx + 1} voted for Trump</div>'


def render_row(idx, row):
    x, y = row.ox, row.oy
    return f"""
    <td style="width: 50%;">
        <h2 class="text">Voter {idx + 1}'s Neighborhood</h2>

        <!-- {render_voter(row, idx)} -->
        <div class="text coordinate"> {render_coordinate(row)}</div>
        <div class="text address"><i>approx.</i> {reverse_geocode(row.x, row.y)}</div>
        {precinct_label(row)}
        <div class="fill">
            <a href="https://maps.google.com/?q={y},{x}&ll={y},{x}&z=8" target="_blank">
                <image src="images/{idx}.png"/>
            </a>
        </div>
    </td>
    """

def render_full_table(selection):
    result = []
    for idx in range(len(selection)):
        row = selection.iloc[idx]
        if row.selected_party == "D":
            result.append([])
        result[-1].append(render_row(idx, row))
    result = ["<tr>" + "\n".join(x) + "</tr>" for x in result]
    return "\n".join(result)
