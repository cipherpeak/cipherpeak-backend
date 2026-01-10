# client/admin.py
from django.contrib import admin
from .models import Client, ClientDocument,ClientPaymentHistory,ClientAdminNote

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin configuration for Client model"""
    
    # Fields to display in the list view
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
    
    # Fields that can be used for filtering
    list_filter = [
        'client_type',
        'industry', 
        'status',
        'onboarding_date',
        'contract_start_date',
        'contract_end_date',
        'created_at'
    ]
    
    # Fields that can be searched
    search_fields = [
        'client_name',
        'owner_name',
        'contact_person_name',
        'contact_email',
        'contact_phone',
        'description'
    ]
    
    # Fields that are read-only
    readonly_fields = ['created_at', 'updated_at', 'total_content_per_month', 'is_active_client', 'contract_duration']
    
    # Fields to display in the detail view with organization
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
            'classes': ('collapse',)  # Makes this section collapsible
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
    
    # Prepopulated fields
    prepopulated_fields = {}
    
    # Date-based hierarchy for navigation
    date_hierarchy = 'created_at'
    
    # Default ordering
    ordering = ['-created_at']
    
    # Actions you can perform on multiple clients
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        """Custom action to mark clients as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} clients were marked as active.')
    
    def mark_as_inactive(self, request, queryset):
        """Custom action to mark clients as inactive"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} clients were marked as inactive.')
    
    mark_as_active.short_description = "Mark selected clients as Active"
    mark_as_inactive.short_description = "Mark selected clients as Inactive"
    
    # Display computed properties in list view
    def total_content_per_month(self, obj):
        return obj.total_content_per_month
    total_content_per_month.short_description = 'Total Content/Month'
    
    def is_active_client(self, obj):
        return obj.is_active_client
    is_active_client.short_description = 'Active'
    is_active_client.boolean = True  # Shows as checkbox


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for ClientDocument model"""
    
    # Fields to display in the list view
    list_display = [
        'title',
        'client',
        'document_type',
        'uploaded_by',
        'uploaded_at',
        'get_file_name'
    ]
    
    # Fields that can be used for filtering
    list_filter = [
        'document_type',
        'client',
        'uploaded_at',
        'uploaded_by'
    ]
    
    # Fields that can be searched
    search_fields = [
        'title',
        'description',
        'client__client_name',
        'uploaded_by__username'
    ]
    
    # Fields that are read-only
    readonly_fields = ['uploaded_at', 'uploaded_by', 'uploaded_at']
    
    # Fields to display in the detail view
    fieldsets = (
        ('Document Information', {
            'fields': (
                'client',
                'document_type',
                'title',
                'file',
                'description'
            )
        }),
        ('Upload Information', {
            'fields': (
                'uploaded_by',
                'uploaded_at'
            )
        }),
    )
    
    # Date-based hierarchy for navigation
    date_hierarchy = 'uploaded_at'
    
    # Default ordering
    ordering = ['-uploaded_at']
    
    # Automatically set the uploaded_by field
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set uploaded_by when creating, not updating
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom method to display file name
    def get_file_name(self, obj):
        return obj.file.name if obj.file else "No file"
    get_file_name.short_description = 'File Name'
    @admin.register(ClientPaymentHistory)
    class ClientPaymentHistoryAdmin(admin.ModelAdmin):
        list_display = [
            'client',
            'payment_date',
            'amount',
            'payment_method',
            'created_at',
            'updated_at'
        ]
       
    @admin.register(ClientAdminNote)
    class ClientAdminNoteAdmin(admin.ModelAdmin):
        list_display = [
            'client',
            'note',
            'created_at',
            'updated_at'
        ]
        

            
        