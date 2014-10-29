from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2 import Geometry
from shapely.geometry.point import Point
from sqlalchemy import event
from collections import Sequence


class Geometric(object):
    pass


@event.listens_for(Geometric, 'mapper_configured', propagate=True)
def configure_geometric(mapper, target):
    for k, column in mapper.columns.items():
        property = getattr(target, k)
        if property.is_attribute and type(column.type) is Geometry:
            if column.type.geometry_type.lower() == 'point':
                setattr(target, k, PointGeometryDescriptor(property))


class PointGeometryDescriptor(object):
    """descriptor for 2D point geometry"""

    def __init__(self, property):
        self.property = property

    def __get__(self, instance, cls=None):
        if instance is not None:
            wkb = self.property.__get__(instance, cls)
            if wkb is None:
                return None
            p = to_shape(wkb)
            p.to_wkb = lambda: wkb
            return p

        elif cls is not None:
            return self.property.__get__(instance, cls)

    def __set__(self, instance, v):
        if len(v) == 2 and isinstance(v[0], Sequence):
            points = v[0]
            srid = v[1]
        else:
            points = v
            srid = None
        p = Point(*points)
        self.property.__set__(instance, from_shape(p, srid=srid))


def Point_repr(point):
    p = [point.x, point.y]
    if point.has_z:
        p.append(point.z)

    return "<Point {}>".format(', '.join(map(str, p)))

Point.__repr__ = Point_repr
