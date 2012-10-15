import csv
from django.http import HttpResponse

def export_as_csv_action(description="Export selected objects as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/1697/
        """
        opts = modeladmin.model._meta
        #field_names = set([field.name for field in opts.fields])
        #if fields:
        #    fieldset = set(fields)
        #    #field_names = field_names & fieldset
        #    field_names = fieldset
        #elif exclude:
        #    excludeset = set(exclude)
        #    field_names = field_names - excludeset

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(opts).replace('.', '_')
        response['ContentType'] = 'application/ms-excel';
        response['ContentEncoding'] =  "big5";

        writer = csv.writer(response)
        #writer.writerow(unicode('\xef\xbb\xbf').encode("utf-8","replace"))
        if header:
            writer.writerow(list(unicode(fields).encoding("big5",replace)))
        for obj in queryset:
            rowdata=list()
            for field in fields:
                if hasattr(getattr(obj, field), '__call__'): 
                    rowdata.append(unicode(getattr(obj, field)()).encoding("big5",replace))
                else: 
                    rowdata.append(unicode(getattr(obj, field)).encoding("big5",replace))
            writer.writerow(rowdata)
        return response
    export_as_csv.short_description = description
    return export_as_csv