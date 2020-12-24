from PIL import Image


def add_watermark(fp, tp):
    im = Image.open(fp)
    # bw = im.convert("L")

    # iconXSize = 160
    # iconYSize = 51

    width, height = im.size
    if width > 640:
        rotate = False
    elif width >= iconXSize:
        rotate = False
    elif width >= iconYSize:
        if height >= iconXSize:
            temp = iconXSize

            iconXSize = iconYSize
            iconYSize = temp
            rotate = True
        else:
            self.logMessage("too small to add a watermark", STATUS_MSG)
            return
    else:
        self.logMessage("too small to add a watermark", STATUS_MSG)
        return

    anchorX = width - iconXSize
    anchorY = height - iconYSize

    nrOfPixels = iconXSize * iconYSize
    sumPixel = 0
    for x in xrange(anchorX, anchorX + iconXSize):
        for y in xrange(anchorY, anchorY + iconYSize):
            sumPixel = sumPixel + bw.getpixel((x, y))

    averagePixel = sumPixel / nrOfPixels

    if averagePixel < 128:
        # its more blackish
        waterIcon = Image.open(self.icon_white)
    else:
        # its more whitish
        waterIcon = Image.open(self.icon_black)

    waterIcon = waterIcon.convert("RGBA")

    if rotate:
        waterIcon = waterIcon.rotate(90, expand=True)

    im.paste(waterIcon, (anchorX, anchorY), waterIcon)
    im.save(tp)
