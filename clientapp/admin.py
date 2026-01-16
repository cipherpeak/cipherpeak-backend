from django.contrib import admin
from .models import Client, ClientDocument, ClientAdminNote, ClientPayment

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    
    class ClientPaymentInline(admin.TabularInline):
        model = ClientPayment
        extra = 0
        readonly_fields = ['created_at', 'updated_at', 'net_amount']
        fields = ['month', 'year', 'amount', 'tax_amount', 'discount', 'net_amount', 'scheduled_date', 'status', 'payment_date', 'payment_method']
        ordering = ['-year', '-month']

    inlines = [ClientPaymentInline]
    
    list_display = [
        'client_name', 
        'client_type', 
        'industry', 
        'status', 
        'contact_person_name',
        'contact_email',
        'onboarding_date',
        'monthly_retainer',
        'total_content_per_month',
        'is_active_client',
        'created_at'
    ]
    
    list_filter = [
        'client_type',
        'industry', 
        'status',
        'onboarding_date',
        'contract_start_date',
        'contract_end_date',
        'created_at'
    ]
    
    search_fields = [
        'client_name',
        'owner_name',
        'contact_person_name',
        'contact_email',
        'contact_phone',
        'description'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'total_content_per_month', 'is_active_client', 'contract_duration']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'client_name', 
                'client_type', 
                'industry', 
                'status',
                'description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'owner_name',
                'contact_person_name', 
                'contact_email', 
                'contact_phone'
            )
        }),
        ('Social Media', {
            'fields': (
                'instagram_id',
                'facebook_id', 
                'youtube_channel',
                'google_my_business',
                'linkedin_url',
                'twitter_handle'
            ),
            'classes': ('collapse',) 
        }),
        ('Content Requirements', {
            'fields': (
                'videos_per_month',
                'posters_per_month', 
                'reels_per_month',
                'stories_per_month',
                'total_content_per_month'
            )
        }),
        ('Contract & Timeline', {
            'fields': (
                'onboarding_date',
                'contract_start_date',
                'contract_end_date',
                'contract_duration'
            )
        }),
        ('Location Information', {
            'fields': (
                'address',
                'city', 
                'state',
                'country',
                'postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Business Information', {
            'fields': (
                'website',
                'business_registration_number',
                'tax_id'
            ),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': (
                'monthly_retainer',
            )
        }),
        ('System Information', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    prepopulated_fields = {}
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):

        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} clients were marked as active.')
    
    def mark_as_inactive(self, request, queryset):
    
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} clients were marked as inactive.')
    
    mark_as_active.short_description = "Mark selected clients as Active"
    mark_as_inactive.short_description = "Mark selected clients as Inactive"
    
    def total_content_per_month(self, obj):
        return obj.total_content_per_month
    total_content_per_month.short_description = 'Total Content/Month'
    
    def is_active_client(self, obj):
        return obj.is_active_client
    is_active_client.short_description = 'Active'
    is_active_client.boolean = True 


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    
    list_display = [
        'client',
        'document_type',
        'uploaded_by',
        'uploaded_at',
        'get_file_name'
    ]
    
    list_filter = [
        'document_type',
        'client',
        'uploaded_at',
        'uploaded_by'
    ]
    
    search_fields = [
        'client__client_name',
        'uploaded_by__username'
    ]
    
    readonly_fields = ['uploaded_at', 'uploaded_by', 'uploaded_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'client',
                'document_type',
                'file',
            )
        }),
        ('Upload Information', {
            'fields': (
                'uploaded_by',
                'uploaded_at'
            )
        }),
    )
    
    date_hierarchy = 'uploaded_at'
    
    ordering = ['-uploaded_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_file_name(self, obj):
        return obj.file.name if obj.file else "No file"
    get_file_name.short_description = 'File Name'

   
@admin.register(ClientAdminNote)
class ClientAdminNoteAdmin(admin.ModelAdmin):
    list_display = [
        'client',
        'note',
        'created_at',
        'updated_at'
    ]
        

@admin.register(ClientPayment)
class ClientPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'client',
        'month',
        'year',
        'amount',
        'status',
        'payment_date',
        'processed_by',
        'created_at'
    ]
    list_filter = ['status', 'month', 'year', 'payment_method']
    search_fields = ['client__client_name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'net_amount']