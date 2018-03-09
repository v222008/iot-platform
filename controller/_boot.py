"""
MIT license
(C) Micropython team
(C) Konstantin Belyalov 2017-2018
"""
import gc
import uos
import flashbdev
import main


print("Booting...")

gc.threshold((gc.mem_free() + gc.mem_alloc()) // 4)

if flashbdev.bdev:
    uos.mount(flashbdev.bdev, '/')

gc.collect()

# Run RGB controller
main.start()
