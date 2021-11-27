import numpy
import svgwrite


class SnowflakeGenerator():

    _default_parameters = {
        "symmetry": 6,
        "global_scale_factor": 200,
        "ray_width": 0.065,  # 0.06,  0.05 is the "extra_thick.gif"
        "comb_width": 0.053,  #
        "min_comb_count": 3,
        "max_comb_count": 5,
        "comb_tip_type": "angled",
        "comb_tip_min_length": 0.15,
        "comb_tip_max_length": 0.45,
        "verbose": False,
    }

    def __init__(s):

        s.__dict__.update(s._default_parameters)
        s.polygon_list = []
        s.rng = numpy.random.default_rng()
        s.rand()

    def rand(s):

        s.polygon_list = []
        s.compute_constants()
        s.compute_primary_ray()
        s.compute_combs()
        s.apply_global_scale_factor()
        s.comb_to_snowflake()

    def compute_constants(s):

        # Angles within the snowflake
        s.theta = 2 * numpy.pi / s.symmetry
        s.half_theta = s.theta / 2

        # Rotation matrix corresponding to theta above
        rot = numpy.empty(shape=(2, 2))
        rot[0][0] = numpy.cos(s.theta)
        rot[1][0] = numpy.sin(s.theta)
        rot[0][1] = -rot[1][0]
        rot[1][1] = rot[0][0]
        s.rot = rot

    def compute_primary_ray(s):
        """Build primary hexagonal ray and add to polygon list"""
        p = numpy.empty(shape=(5, 2))  # polygon

        half_ray_width = s.ray_width / 2
        tip = half_ray_width * numpy.tan(s.half_theta)

        # clockwise from lower right
        p[0] = (1 - tip, -half_ray_width)
        p[1] = (0, -half_ray_width)
        p[2] = (0, half_ray_width)
        p[3] = (1 - tip, half_ray_width)
        p[4] = (1, 0)
        s.polygon_list.append(p)

        for i in range(s.symmetry - 1):
            p = numpy.copy(p)
            # Using einsum instead of reshaping as col vec for s.rot*p
            p[0] = numpy.einsum("ji,i->j", s.rot, p[0])
            p[1] = numpy.einsum("ji,i->j", s.rot, p[1])
            p[2] = numpy.einsum("ji,i->j", s.rot, p[2])
            p[3] = numpy.einsum("ji,i->j", s.rot, p[3])
            p[4] = numpy.einsum("ji,i->j", s.rot, p[4])
            s.polygon_list.append(p)

    def compute_combs(s):

        s.comb_count = s.rng.integers(s.min_comb_count, s.max_comb_count + 1)

        l_i = s.rng.random(size=s.comb_count)
        l_i = (
            s.comb_tip_max_length - s.comb_tip_min_length
        ) * l_i + s.comb_tip_min_length

        dx = 1.0 / (s.comb_count + 1)  # interval - no comb on 0 or end.
        p = numpy.empty(shape=(2, 2))
        w = numpy.asarray([s.comb_width, 0])

        if s.verbose:
            print("Creating comb_count {} combs".format(s.comb_count))
            print(" Random comb lengths: {}".format(l_i))

        if s.comb_tip_type == "angled":

            if s.verbose:
                print("Building combs with angled shape")

            # precompute coordinates of 'line' for edge of each comb
            c = numpy.empty(shape=(2, 2))
            c[0] = (0, 0)
            c[1] = (numpy.cos(s.theta), numpy.sin(s.theta))

            for i, l in enumerate(l_i):
                p = numpy.empty(shape=(5, 2))
                tr = (i + 1) * dx  # no comb at 0
                t = numpy.asarray((tr, 0))  # translation vector

                l = min(0.9 * tr, l)

                p[0] = c[0] + t
                p[1] = c[1] * l + t
                p[2] = p[1] + w / 2  # comb tip
                p[3] = (
                    p[2] + w / 2 - c[1] * s.comb_width / 2
                )  # Only "correct" for 6-fold rip
                p[4] = p[0] + w
                s.polygon_list.append(p)
                if s.verbose:
                    print("Comb {}, length {}, vertices {}".format(i, l, p))
        else:
            msg = "comb_tip_type '{}' not recognized or implemented".format(
                s.comb_tip_type
            )
            # ValueError or TypeError depends on whether or not you consider
            # the set of valid input strings an enum or a generic string.
            raise TypeError(msg)

    def comb_to_snowflake(s):
        """
        Mirror the comb across x-axis and apply c-fold rotational symmetry.
        """

        # mirror comb
        mirrs = []
        for p in s.polygon_list[s.symmetry:]:
            mirrs.append(numpy.copy(p))
            mirrs[-1][:, 1] = -mirrs[-1][:, 1]
        s.polygon_list += mirrs

        # low-perf - consider refactor into numpy arrays and not lists
        for i in range(s.symmetry - 1):
            rp = []
            for p in s.polygon_list[-2 * s.comb_count:]:
                rv = []
                for v in p:
                    rv.append(numpy.einsum("ji,i->j", s.rot, v))
                rp.append(numpy.asarray(rv))
            s.polygon_list += rp

    def apply_rotation(s):
        pass

    def apply_global_scale_factor(s):

        for polygon in s.polygon_list:
            polygon *= s.global_scale_factor

    def to_svg(s, output_path="test.svg"):
        """Write to SVG"""
        L = s.global_scale_factor * (1 + s.comb_tip_max_length)
        # A bit too big - refine if need be.
        d = svgwrite.Drawing(output_path, profile="tiny", size=(2 * L, 2 * L))
        polys = d.add(d.g(id="polys"))  # set fillcolor later.

        for p in s.polygon_list:
            dp = d.polygon(p)
            polys.add(dp)

        # Translate the polys L,L to get them within the box.
        # I have no idea why I couldn't set a viewBox instead,
        polys.translate(L, L)

        d.save()


if __name__ == "__main__":

    num_flakes = 10
    sg = SnowflakeGenerator()
    sg.symmetry = 7

    for i in range(num_flakes):
        print("Iteration {}".format(i))
        sg.rand()
        sg.to_svg("img/{}.svg".format(i))
