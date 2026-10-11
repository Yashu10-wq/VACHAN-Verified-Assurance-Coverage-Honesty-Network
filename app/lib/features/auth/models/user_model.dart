enum UserRole {
  customer('CUSTOMER'),
  insuranceAgent('INSURANCE_AGENT'),
  approvalAuthority('APPROVAL_AUTHORITY');

  final String value;
  const UserRole(this.value);

  static UserRole fromString(String? role) {
    switch (role?.toUpperCase()) {
      case 'INSURANCE_AGENT':
        return UserRole.insuranceAgent;
      case 'APPROVAL_AUTHORITY':
        return UserRole.approvalAuthority;
      case 'CUSTOMER':
      default:
        return UserRole.customer;
    }
  }

  String get displayName {
    switch (this) {
      case UserRole.customer:
        return 'Customer';
      case UserRole.insuranceAgent:
        return 'Insurance Agent';
      case UserRole.approvalAuthority:
        return 'Approval Authority';
    }
  }
}

enum AccountStatus {
  pendingVerification('PENDING_VERIFICATION'),
  pendingApproval('PENDING_APPROVAL'),
  active('ACTIVE'),
  suspended('SUSPENDED'),
  rejected('REJECTED');

  final String value;
  const AccountStatus(this.value);

  static AccountStatus fromString(String? status) {
    switch (status?.toUpperCase()) {
      case 'PENDING_APPROVAL':
        return AccountStatus.pendingApproval;
      case 'ACTIVE':
        return AccountStatus.active;
      case 'SUSPENDED':
        return AccountStatus.suspended;
      case 'REJECTED':
        return AccountStatus.rejected;
      case 'PENDING_VERIFICATION':
      default:
        return AccountStatus.pendingVerification;
    }
  }

  String get displayName {
    switch (this) {
      case AccountStatus.pendingVerification:
        return 'Pending Verification';
      case AccountStatus.pendingApproval:
        return 'Pending Approval';
      case AccountStatus.active:
        return 'Active';
      case AccountStatus.suspended:
        return 'Suspended';
      case AccountStatus.rejected:
        return 'Rejected';
    }
  }
}

class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String? phone;
  final UserRole role;
  final AccountStatus accountStatus;
  final String? emailVerifiedAt;
  final String? createdAt;

  const UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    required this.role,
    required this.accountStatus,
    this.emailVerifiedAt,
    this.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      phone: json['phone'] as String?,
      role: UserRole.fromString(json['role'] as String?),
      accountStatus: AccountStatus.fromString(json['account_status'] as String?),
      emailVerifiedAt: json['email_verified_at'] as String?,
      createdAt: json['created_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'phone': phone,
      'role': role.value,
      'account_status': accountStatus.value,
      'email_verified_at': emailVerifiedAt,
      'created_at': createdAt,
    };
  }

  UserModel copyWith({
    String? id,
    String? email,
    String? fullName,
    String? phone,
    UserRole? role,
    AccountStatus? accountStatus,
    String? emailVerifiedAt,
    String? createdAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      phone: phone ?? this.phone,
      role: role ?? this.role,
      accountStatus: accountStatus ?? this.accountStatus,
      emailVerifiedAt: emailVerifiedAt ?? this.emailVerifiedAt,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
