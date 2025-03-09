from datetime import datetime
from general.forms import ApprovalLogForm
from general.models import ApprovalLog, Status


class Approval:

    def log_entry(self, obj=None, ref='', user=None, notes="", status=None, status_message=None):        
        data = {
            'model'                     : obj._meta.object_name,
            'ref_id'                    : obj.id,
            'reference'                 : ref,
            'approved_rejected_by'      : user,
            'approved_rejected_date'    : datetime.now(),
            'approved_rejected_note'    : notes,
            'status'                    : status,
            'status_message'            : status_message
        }
        approval_form                   = ApprovalLogForm(data)
        if approval_form.is_valid()     : approval_form.save()
        else:
            for field in approval_form:
                for error in field.errors:
                    print('error xyz: ', error)

    def get_approval_logs(self, reference=None, ref_id=None, all_status=False):
        approvals = ApprovalLog.objects.filter(reference=reference, ref_id=ref_id).order_by("approved_rejected_date")
        if not all_status : approvals = approvals.exclude(status=Status.name("started"))
        return approvals