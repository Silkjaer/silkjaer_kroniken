"""The light table: where each paragraph of the 1913 transcripts stands on the photographed pages.

Measured by eye on the cropped photographs (billeder/1913/fuld): y in per cent of the page height at the left edge of
the writing, for the centre of the first and the last line of each paragraph on each page. SL is how much lower the
right end of a line lies than its left end (per cent of height), at the top and at the bottom of the writing on that
page — the pages curve, so the slant changes down the page. PI is the line pitch. The transcripts are listed in the
order they stand in chapter 12; each lists its source paragraphs in order (editorial notes after them are not mapped).
"""
LT = [
    # Thomas' forklaring 28. februar
    {'pages': ['pp-148R', 'pp-149L'], 'paras': [
        [('pp-148R', 9.5, 64.6)],
        [('pp-148R', 68.1, 95.6), ('pp-149L', 10.0, 73.0)],
        [('pp-149L', 75.6, 97.6)]]},
    # Kristianes forklaring 7. marts
    {'pages': ['pp-153L', 'pp-153R', 'pp-154L', 'pp-154R', 'pp-155L'], 'paras': [
        [('pp-153L', 16.9, 82.6), ('pp-153R', 7.9, 99.3), ('pp-154L', 8.1, 15.0)],
        [('pp-154L', 18.0, 97.7), ('pp-154R', 3.5, 20.5)],
        [('pp-154R', 22.5, 53.0)],
        [('pp-154R', 55.8, 99.2), ('pp-155L', 5.5, 15.3)],
        [('pp-155L', 15.3, 96.5)]]},
    # bidragssagen 36/13, samme retsdag
    {'pages': ['pp-155R', 'pp-156L', 'pp-156R'], 'paras': [
        [('pp-155R', 8.0, 18.0)],
        [('pp-155R', 19.4, 27.6)],
        [('pp-155R', 30.4, 38.6)],
        [('pp-155R', 41.4, 98.6), ('pp-156L', 5.5, 27.5)],
        [('pp-156L', 31.0, 78.0)],
        [('pp-156L', 81.5, 97.0), ('pp-156R', 17.0, 76.5)],
        [('pp-156R', 79.5, 79.5)],
        [('pp-156R', 82.0, 95.0)],
        [('pp-156R', 97.5, 97.5)]]},
    # Kristine Olines forklaring, retten i Årgab 17. marts
    {'pages': ['rp-72', 'rp-73L', 'rp-73R', 'rp-74L'], 'paras': [
        [('rp-72', 5.5, 49.0)],
        [('rp-72', 53.0, 99.5)],
        [('rp-73L', 5.0, 54.5)],
        [('rp-73L', 54.5, 96.5), ('rp-73R', 2.5, 10.0)],
        [('rp-73R', 10.0, 89.0)],
        [('rp-73R', 89.0, 94.0), ('rp-74L', 10.0, 96.0)]]},
    # rapport A, 17. februar
    {'pages': ['ra-1', 'ra-2', 'ra-3', 'ra-4', 'ra-5', 'ra-6', 'ra-7', 'ra-8'], 'paras': [
        [('ra-1', 7.0, 24.0)],
        [('ra-1', 30.5, 63.5)],
        [('ra-1', 66.5, 96.0), ('ra-2', 10.0, 96.5), ('ra-3', 10.0, 10.0)],
        [('ra-3', 14.0, 96.5)],
        [('ra-4', 7.0, 97.0), ('ra-5', 5.5, 32.5)],
        [('ra-5', 35.5, 71.0)],
        [('ra-5', 74.0, 96.5), ('ra-6', 5.0, 90.5)],
        [('ra-7', 4.0, 21.5)],
        [('ra-7', 25.0, 89.0)],
        [('ra-7', 89.0, 89.0), ('ra-8', 14.0, 60.5)],
        [('ra-8', 69.0, 90.0)]]},
    # erkendelsen 22. marts og § 174-frafaldet 26. marts
    {'pages': ['pp-174L', 'pp-174R', 'pp-177L', 'pp-177R'], 'paras': [
        [('pp-174L', 11.0, 95.0), ('pp-174R', 18.0, 49.5)],
        [('pp-174R', 55.0, 94.0)],
        [('pp-177L', 16.0, 82.0), ('pp-177R', 8.0, 96.5)]]},
    # Kamps indlæg 3. april
    {'pages': ['kamp-1', 'kamp-2', 'kamp-3', 'kamp-4', 'kamp-5', 'kamp-6'], 'paras': [
        [('kamp-1', 24.0, 48.0)],
        [('kamp-1', 52.5, 62.5)],
        [('kamp-1', 65.5, 98.0), ('kamp-2', 2.5, 70.5)],
        [('kamp-2', 73.5, 91.5)],
        [('kamp-2', 95.5, 98.5), ('kamp-3', 1.0, 23.5)],
        [('kamp-3', 27.0, 29.5)],
        [('kamp-3', 33.0, 57.5)],
        [('kamp-3', 61.0, 99.0), ('kamp-4', 1.0, 99.5), ('kamp-5', 1.0, 27.0)],
        [('kamp-5', 31.0, 74.0)],
        [('kamp-5', 77.5, 99.0), ('kamp-6', 1.0, 12.5)],
        [('kamp-6', 16.0, 19.5)],
        [('kamp-6', 23.0, 40.0)],
        [('kamp-6', 43.0, 69.0)],
        [('kamp-6', 71.5, 78.5)],
        [('kamp-6', 86.0, 97.0)]]},
    # dommen 14. april
    {'pages': ['dp-102L', 'dp-102R'], 'paras': [
        [('dp-102L', 3.0, 14.0)],
        [('dp-102L', 17.0, 55.5)],
        [('dp-102L', 56.0, 72.0)],
        [('dp-102L', 75.0, 99.0), ('dp-102R', 7.0, 41.0)],
        [('dp-102R', 42.0, 88.0)]]},
]
SL = {'pp-148R': (7.1, -6.2), 'pp-149L': (-5.2, -1.4), 'pp-153L': (6.8, 16.0), 'pp-153R': (-3.9, -3.2), 'pp-154L': (-5.1, -1.9),
      'pp-154R': (-2.0, -3.0), 'pp-155L': (-7.0, -2.0), 'pp-155R': (3.3, -4.1), 'pp-156L': (-5.0, 0.0), 'pp-156R': (8.0, -2.0),
      'rp-72': (4.0, 1.5), 'rp-73L': (-2.4, -2.4), 'rp-73R': (-3.75, -5.6), 'rp-74L': (-6.5, -2.0),
      'ra-1': (0, 0), 'ra-2': (0, 2), 'ra-3': (0, 0), 'ra-4': (-2, -1.5), 'ra-5': (0, 0), 'ra-6': (0, 1), 'ra-7': (-1.5, 0), 'ra-8': (-7, -4),
      'pp-174L': (-1, 4), 'pp-174R': (5, 1), 'pp-177L': (-5, 16), 'pp-177R': (13, 2),
      'kamp-1': (1, 1), 'kamp-2': (-3.5, -1.5), 'kamp-3': (0, 0), 'kamp-4': (0, 0), 'kamp-5': (1, 1), 'kamp-6': (0, 0),
      'dp-102L': (-4, -3.5), 'dp-102R': (12, 2)}
PI = {'pp-148R': 3.45, 'pp-149L': 2.43, 'pp-153L': 7.3, 'pp-153R': 2.86, 'pp-154L': 2.8, 'pp-154R': 2.24, 'pp-155L': 2.7,
      'pp-155R': 2.65, 'pp-156L': 3.1, 'pp-156R': 3.6, 'rp-72': 4.8, 'rp-73L': 3.7, 'rp-73R': 3.75, 'rp-74L': 7.0,
      'ra-1': 3.24, 'ra-2': 3.24, 'ra-3': 3.12, 'ra-4': 3.22, 'ra-5': 3.24, 'ra-6': 3.13, 'ra-7': 3.1, 'ra-8': 10.0,
      'pp-174L': 4.6, 'pp-174R': 6.4, 'pp-177L': 8.0, 'pp-177R': 4.4,
      'kamp-1': 3.3, 'kamp-2': 3.25, 'kamp-3': 3.25, 'kamp-4': 3.2, 'kamp-5': 3.1, 'kamp-6': 3.2,
      'dp-102L': 1.7, 'dp-102R': 4.0}
