from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2 import Geometry
from shapely.geometry import Point, MultiPolygon, Polygon
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

            if column.type.geometry_type.lower() == 'multipolygon':
                setattr(target, k, MultiPolygonGeometryDescriptor(property))


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
        if isinstance(v, Point):
            self.property.__set__(instance, from_shape(v, srid=4326))
        else:
            if len(v) == 2 and isinstance(v[0], Sequence):
                points = v[0]
                srid = v[1]
            else:
                points = v
                srid = None
            p = Point(*points)
            self.property.__set__(instance, from_shape(p, srid=srid))


class MultiPolygonGeometryDescriptor(object):
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
        if isinstance(v, MultiPolygon):
            # TODO: read SRID from column and copy
            self.property.__set__(instance, from_shape(v, srid=4326))
        elif isinstance(v, Polygon):
            # TODO: read SRID from column and copy
            mp = MultiPolygon(*[v.poly.boundary.coords])
            self.property.__set__(instance, from_shape(mp, srid=4326))
        else:
            if isinstance(v[-1], Sequence):
                points = v
                srid = None
            else:
                points = v[:-1]
                srid = v[-1]
            p = MultiPolygon(*points)
            self.property.__set__(instance, from_shape(p, srid=srid))


def Point_repr(point):
    p = [point.x, point.y]
    if point.has_z:
        p.append(point.z)

    return "<Point ({})>".format(', '.join(map(str, p)))


def MultiPolygon_repr(polygon):
    p = polygon.bounds
    return "<MultiPolygon ({})>".format(', '.join(map(str, p)))

Point.__repr__ = Point_repr
MultiPolygon.__repr__ = MultiPolygon_repr
