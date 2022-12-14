# -*- coding: utf-8 -*-


import string
import re
import sass
import json

from django.utils.translation import ugettext as _
from django.urls import reverse
from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from stormwater.models import PolygonalMapFeature

from treemap.models import User, Species, StaticPage, Instance, Boundary, Tree, Plot

from treemap.plugin import get_viewable_instances_filter

from treemap.lib.user import get_audits, get_audits_params
from treemap.lib import COLOR_RE
from treemap.lib.perms import model_is_creatable
from treemap.lib.object_caches import udf_defs
from treemap.units import get_unit_abbreviation, get_units
from treemap.util import leaf_models_of_class, get_field
from treemap.images import get_image_from_request


_SCSS_VAR_NAME_RE = re.compile('^[_a-zA-Z][-_a-zA-Z0-9]*$')


def edits(request, instance):
    """
    Request a variety of different audit types.
    Params:
       - models
         Comma separated list of models (only Tree and Plot are supported)
       - model_id
         The ID of a specfici model. If specified, models must also
         be defined and have only one model

       - user
         Filter by a specific user

       - exclude (default: true)
         Set to false to ignore edits that are currently pending

       - page_size
         Size of each page to return (up to PAGE_MAX)
       - page
         The page to return
    """
    params = get_audits_params(request)

    user_id = request.GET.get('user', None)
    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)

    return get_audits(request.user, instance, request.GET.copy(), user,
                      **params)


def index(request, instance):
    return HttpResponseRedirect(reverse('react_map_index', kwargs={
        'instance_url_name': instance.url_name}))
    #return HttpResponseRedirect(reverse('map', kwargs={
    #    'instance_url_name': instance.url_name}))


def get_map_view_context(request, instance):
    if request.user and not request.user.is_anonymous:
        iuser = request.user.get_effective_instance_user(instance)
        resource_classes = [resource for resource in instance.resource_classes
                            if model_is_creatable(iuser, resource)]
    else:
        resource_classes = []

    context = {
        'resource_classes': resource_classes,
        'only_one_resource_class': len(resource_classes) == 1,
        'polygon_area_units': get_unit_abbreviation(
            get_units(instance, 'greenInfrastructure', 'area')),
        'q': request.GET.get('q'),
    }
    add_plot_field_groups(
        context,
        instance,
        filter_fields=['tree.id', 'tree.species', 'tree.diameter']
    )

    add_map_info_to_context(context, instance)
    return context


def get_plot_field_groups(request, instance):
    context = {}
    _get_plot_field_groups(
        context,
        instance,
        request.user,
        filter_fields=['tree.id']
        #filter_fields=['tree.id', 'tree.species', 'tree.diameter']
    )
    return context


def map_save_image_with_label(request, instance, label):
    """
    Save an image with this label in the session.
    This is needed when a user is creating a new tree from the website
    """
    data = get_image_from_request(request)
    request.session[label] = data
    return


def add_map_info_to_context(context, instance):
    all_polygon_types = {c.map_feature_type
                         for c in leaf_models_of_class(PolygonalMapFeature)}
    my_polygon_types = set(instance.map_feature_types) & all_polygon_types
    context['has_polygons'] = len(my_polygon_types) > 0
    context['has_boundaries'] = instance.boundaries.exists()


def static_page(request, instance, page):
    static_page = StaticPage.get_or_new(instance, page)

    return {'content': static_page.content,
            'title': static_page.name}


def boundary_to_geojson(request, instance, boundary_id):
    boundary = get_object_or_404(Boundary.all_objects, pk=boundary_id)
    geom = boundary.geom

    # Leaflet prefers to work with lat/lng so we do the transformation
    # here, since it way easier than doing it client-side
    geom.transform('4326')
    return HttpResponse(geom.geojson)


def add_anonymous_boundary(request):
    request_dict = json.loads(request.body)
    srid = request_dict.get('srid', 4326)
    polygon = Polygon(request_dict.get('polygon', []), srid=srid)
    if srid != 3857:
        polygon.transform(3857)
    b = Boundary.anonymous(polygon)
    b.save()
    return {'id': b.id}


def boundary_autocomplete(request, instance):
    max_items = request.GET.get('max_items', None)
    max_items = int(max_items) if max_items else None

    boundaries = instance.boundaries \
                         .filter(searchable=True) \
                         .order_by('sort_order', 'name')[:max_items]

    return [{'name': boundary.name,
             'category': boundary.category,
             'id': boundary.pk,
             'value': boundary.name,
             'tokens': boundary.name.split(),
             'sortOrder': boundary.sort_order}
            for boundary in boundaries]


def species_list_common(request, instance):
    return species_list(request, instance, is_common=True)


def species_list(request, instance, is_common=False):
    max_items = request.GET.get('max_items', None)
    max_items = int(max_items) if max_items else None

    species_qs = instance.scope_model(Species)\
                         .order_by('common_name')\
                         .values('common_name', 'genus', 'species', 'cultivar',
                                 'other_part_of_name', 'is_common', 'id')

    is_common = request.GET.get('is_common', None)
    is_common = bool(is_common) if is_common else False

    # if this is false, we want to grab everything
    if is_common:
        species_qs = species_qs.filter(is_common=True)

    if max_items:
        species_qs = species_qs[:max_items]

    # Split names by space so that "el" will match common_name="Delaware Elm"
    def tokenize(species):
        names = (species['common_name'],
                 species['genus'],
                 species['species'],
                 species['cultivar'],
                 species['other_part_of_name'])

        tokens = set()

        for name in names:
            if name:
                tokens = tokens.union(name.split())

        # Names are sometimes in quotes, which should be stripped
        return {token.strip(string.punctuation) for token in tokens}

    def annotate_species_dict(sdict):
        sci_name = Species.get_scientific_name(sdict['genus'],
                                               sdict['species'],
                                               sdict['cultivar'],
                                               sdict['other_part_of_name'])

        display_name = "%s [%s]" % (sdict['common_name'],
                                    sci_name)

        tokens = tokenize(sdict)

        sdict.update({
            'scientific_name': sci_name,
            'value': display_name,
            'tokens': tokens})

        return sdict

    return [annotate_species_dict(species) for species in species_qs]


def compile_scss(request):
    """
    Reads key value pairs from the query parameters and adds them as scss
    variables with color values, then imports the main entry point to our scss
    file.

    Any variables provided will be put in the scss file, but only those which
    override variables with '!default' in our normal .scss files should have
    any effect
    """
    # Webpack and libsass have different opinions on how url(...) works
    scss = "$staticUrl: '/static/';\n"
    # We can probably be a bit looser with what we allow here in the future if
    # we need to, but we must do some checking so that libsass doesn't explode
    for key, value in list(request.GET.items()):
        if _SCSS_VAR_NAME_RE.match(key) and COLOR_RE.match(value):
            scss += '$%s: #%s;\n' % (key, value)
        elif key == 'url':
            # Ignore the cache-buster query parameter
            continue
        else:
            raise ValidationError("Invalid SCSS values %s: %s" % (key, value))
    scss += '@import "%s";' % settings.SCSS_ENTRY
    scss = scss.encode('utf-8')

    return sass.compile(string=scss, include_paths=[settings.SCSS_ROOT])


def public_instances_geojson(request):
    def instance_geojson(instance):
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [instance.center_lat_lng.x,
                                instance.center_lat_lng.y]
            },
            'properties': {
                'name': instance.name,
                'url': reverse(
                    'instance_index_view',
                    kwargs={'instance_url_name': instance.url_name}),
                'plot_count': instance.plot_count()
            }
        }

    instances = (Instance.objects
                 .filter(is_public=True)
                 .filter(get_viewable_instances_filter()))

    return [instance_geojson(instance) for instance in instances]


def error_page(status_code):
    template = '%s.html' % status_code

    def inner_fn(request, exception=None):
        reasons = {
            404: _('URL or resource not found'),
            500: _('An unhandled error occured'),
            503: _('Resource is temporarily unavailable')
        }

        # API requests with an unhandled error should return JSON, not HTML
        if ((request.path.startswith('/api/') or
             'application/json' in request.META.get('HTTP_ACCEPT', ''))):
            response = HttpResponse(json.dumps(
                {'status': 'Failure', 'reason': reasons[status_code]}),
                content_type='application/json')
        else:
            response = render(request, template)

        response.status_code = status_code
        return response

    return inner_fn


def add_plot_field_groups(context, instance, filter_fields=None, json=False):
    _filter_fields = filter_fields or []
    templates = {
        "tree.id": "treemap/field/tree_id_tr.html",
        "tree.species": "treemap/field/species_tr.html",
        "tree.diameter": "treemap/field/diameter_tr.html"
    }

    labels = {
        # 'plot-species' is used as the "label" in the 'field' tag,
        # but ulitmately gets used as an identifier in the template
        "tree.species": "plot-species",
        "tree.diameter": _("Trunk Diameter")
    }

    # use the tree if it exists to get the UDF fields, otherwise use a blank tree
    _tree = context.get('tree', Tree())
    labels.update({
        v: k for k, v in _tree.scalar_udf_names_and_fields})

    # use the plot if it exists to get the UDF fields, otherwise use a blank plot
    _plot = context.get('plot', Plot())
    labels.update({
        v: k for k, v in _plot.scalar_udf_names_and_fields})

    def info(group):
        group['fields'] = [
            (field, labels.get(field),
             templates.get(field, "treemap/field/tr.html"))
            for field in group.get('field_keys', []) if field not in _filter_fields
        ]
        group['collection_udfs'] = [
            next(udf for udf in udf_defs(instance)
                 if udf.full_name == udf_name)
            for udf_name in group.get('collection_udf_keys', [])
        ]

        # the UDF model by default is not serializable, so for API calls
        # we force it to be serializable
        if json:
            group['collection_udfs'] = [
                model_to_dict(udf) for udf in group['collection_udfs']]

        return group

    context['field_groups'] = [
        info(group) for group in instance.web_detail_fields]


def _get_plot_field_groups(context, instance, user, filter_fields=None):
    _filter_fields = filter_fields or []

    labels = {
        # 'plot-species' is used as the "label" in the 'field' tag,
        # but ulitmately gets used as an identifier in the template
        "tree.species": "plot-species",
        "tree.diameter": _("Trunk Diameter")
    }

    # use the tree if it exists to get the UDF fields, otherwise use a blank tree
    _tree = context.get('tree', Tree(instance=instance))
    labels.update({
        v: k for k, v in _tree.scalar_udf_names_and_fields})

    # use the plot if it exists to get the UDF fields, otherwise use a blank plot
    _plot = context.get('plot', Plot(instance=instance))
    labels.update({
        v: k for k, v in _plot.scalar_udf_names_and_fields})

    def info(group):
        model = _tree if group['model'] == 'tree' else _plot

        # this is the case when creating these fields for some reason
        user = None
        group['fields'] = [
            get_field(context, labels.get(field), field, user, instance, model=model)
            for field in group.get('field_keys', []) if field not in _filter_fields
        ]

        # the UDF model by default is not serializable, so for API calls
        # we force it to be serializable
        group['collection_udfs'] = [
            next(model_to_dict(udf) for udf in udf_defs(instance)
                 if udf.full_name == udf_name)
            for udf_name in group.get('collection_udf_keys', [])
        ]
        return group

    context['field_groups'] = [
        info(group) for group in instance.web_detail_fields]
