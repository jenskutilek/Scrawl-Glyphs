# Adds random Scrawl data to the current layer

from random import randint

pid = "de.kutilek.Scrawl"
s = 5
data = [
    (
        randint(
            int(round(-100 / s)),
            int(round((Layer.width + 100) / s)),
        ),
        randint(
            int(round(Layer.parent.parent.masters[Layer.parent.parent.selectedFontMaster.id].descender / s)),
            int(round(Layer.parent.parent.masters[Layer.parent.parent.selectedFontMaster.id].ascender / s)),
        ),
    )
    for i in range(2000)
]
Layer.userData["%s.unit" % pid] = s
Layer.userData["%s.data" % pid] = data

#print Layer.userData
