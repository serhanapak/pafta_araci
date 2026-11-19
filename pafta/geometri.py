"""Paylaşılan, dar kapsamlı geometri ölçüm yardımcıları."""

import math


def dikdortgen_kenar_olculeri(polyline):
    """Kapalı, düz kenarlı gerçek bir dikdörtgenin kenarlarını döndür.

    Sonuç (kısa, uzun) biçimindedir. Dört kenarlı olmayan, eğri segment
    (bulge) içeren veya dikdörtgen koşullarını sağlamayan şekiller için
    ``None`` döner; böylece çevreleyen kutu ölçüsü kesin kesit ölçüsü sanılmaz.
    """
    if not polyline.closed:
        return None

    vertices = list(polyline.get_points("xyb"))
    if any(abs(float(point[2])) > 1e-12 for point in vertices):
        return None

    points = [(float(point[0]), float(point[1])) for point in vertices]
    if len(points) < 4:
        return None

    # Bazı DXF üreticileri kapalı polyline'da ilk köşeyi son köşede tekrarlar.
    extent = max(
        max(point[0] for point in points) - min(point[0] for point in points),
        max(point[1] for point in points) - min(point[1] for point in points),
        1.0,
    )
    duplicate_tolerance = extent * 1e-12
    if math.dist(points[0], points[-1]) <= duplicate_tolerance:
        points.pop()
    if len(points) != 4:
        return None

    edges = [
        (
            points[(index + 1) % 4][0] - points[index][0],
            points[(index + 1) % 4][1] - points[index][1],
        )
        for index in range(4)
    ]
    lengths = [math.hypot(*edge) for edge in edges]
    scale = max(lengths)
    if scale == 0 or min(lengths) <= scale * 1e-12:
        return None

    # Dikdörtgenin karşılıklı kenarları eşit ve zıt yönlüdür.
    vector_tolerance = scale * 1e-9
    for first, opposite in ((edges[0], edges[2]), (edges[1], edges[3])):
        if math.hypot(first[0] + opposite[0], first[1] + opposite[1]) > vector_tolerance:
            return None

    # Komşu kenarlar dik olmalıdır; normalize edilmiş skaler çarpım hatasını ölçer.
    dot = edges[0][0] * edges[1][0] + edges[0][1] * edges[1][1]
    if abs(dot) > lengths[0] * lengths[1] * 1e-9:
        return None

    side_a = (lengths[0] + lengths[2]) / 2.0
    side_b = (lengths[1] + lengths[3]) / 2.0
    return (min(side_a, side_b), max(side_a, side_b))
