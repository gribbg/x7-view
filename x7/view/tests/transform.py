from x7.geom.geom import BBox, Point
from x7.geom.transform import Transform


def transform_bbox(start: BBox, target: BBox):
    """Generate a matrix to transform start BBox into target BBox"""
    t = Transform()
    t.translate(target.xl, target.yl)
    t.scale(target.width/start.width, target.height/start.height)
    t.translate(-start.xl, -start.yl)
    return t


def transform_rotate_about(center: Point, angle):
    """Generate rotational transformation centered at center"""
    t = Transform()
    t.translate(*center)
    t.rotate(angle)
    t.translate(*-center)
    return t


def test(start: BBox, target: BBox):
    print(start, target)
    t = transform_bbox(start, target)
    print(' -> ', t)
    print(start.p1, target.p1, ' == ', t.transform_pt(start.p1))
    print(start.p2, target.p2, ' == ', t.transform_pt(start.p2))

    t = transform_rotate_about(start.center, 45)
    print(' -> ', t)
    print(start.p1, start.p2, ' => ', t.transform_pt(start.p1).round(8))
    print(start.p2, start.p1, ' => ', t.transform_pt(start.p2).round(8))
    start = target
    t = transform_rotate_about(start.center, 180)
    print(' -> ', t)
    print(start.p1, start.p2, ' => ', t.transform_pt(start.p1).round(8))
    print(start.p2, start.p1, ' => ', t.transform_pt(start.p2).round(8))


test(BBox(1, 1, 2, 2), BBox(2, 2, 3, 3))
test(BBox(1, 1, 2, 2), BBox(1, 1, 11, 21))
