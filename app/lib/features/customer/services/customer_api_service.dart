import '../../../core/network/api_client.dart';
import '../models/claim_model.dart';
import '../models/customer_policy_model.dart';
import '../models/verification_report_model.dart';

class CustomerApiService {
  final ApiClient apiClient;

  CustomerApiService({required this.apiClient});

  // Policies
  Future<List<DetailedPolicyModel>> listPolicies({String? category}) async {
    try {
      final response = await apiClient.dio.get(
        '/policies',
        queryParameters: category != null ? {'category': category} : null,
      );
      final list = (response.data as List)
          .map((item) => DetailedPolicyModel.fromJson(item as Map<String, dynamic>))
          .toList();
      return list;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<DetailedPolicyModel> getPolicyDetails(String policyId) async {
    try {
      final response = await apiClient.dio.get('/policies/$policyId');
      return DetailedPolicyModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // Registrations
  Future<List<CustomerRegistrationModel>> listRegistrations({String? status}) async {
    try {
      final response = await apiClient.dio.get(
        '/registrations',
        queryParameters: status != null ? {'status': status} : null,
      );
      final rawList = response.data as List;
      final registrations = <CustomerRegistrationModel>[];
      for (final item in rawList) {
        registrations.add(CustomerRegistrationModel.fromJson(item as Map<String, dynamic>));
      }
      return registrations;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<CustomerRegistrationModel> getRegistrationDetails(String registrationId) async {
    try {
      final response = await apiClient.dio.get('/registrations/$registrationId');
      return CustomerRegistrationModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<CustomerRegistrationModel> confirmRegistration(String registrationId) async {
    try {
      final response = await apiClient.dio.post('/registrations/$registrationId/confirm');
      return CustomerRegistrationModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<CustomerRegistrationModel> declineRegistration(String registrationId) async {
    try {
      final response = await apiClient.dio.post('/registrations/$registrationId/decline');
      return CustomerRegistrationModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // Claims
  Future<List<ClaimModel>> listClaims({String? status}) async {
    try {
      final response = await apiClient.dio.get(
        '/claims',
        queryParameters: status != null ? {'status': status} : null,
      );
      return (response.data as List)
          .map((item) => ClaimModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<ClaimModel> getClaimDetails(String claimId) async {
    try {
      final response = await apiClient.dio.get('/claims/$claimId');
      return ClaimModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<ClaimModel> submitClaim({
    required String registrationId,
    required String claimCategory,
    required double requestedAmount,
    required String incidentDate,
    required String description,
    Map<String, dynamic> structuredDetails = const {},
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/claims',
        data: {
          'registration_id': registrationId,
          'claim_category': claimCategory,
          'requested_amount': requestedAmount,
          'incident_date': incidentDate,
          'description': description,
          'structured_details': structuredDetails,
        },
      );
      return ClaimModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // Policy Verification Reports
  Future<VerificationReportModel?> getSessionVerification(String sessionId) async {
    try {
      final response = await apiClient.dio.get('/sales-sessions/$sessionId/verification');
      return VerificationReportModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      // 404 or missing report is handled gracefully
      return null;
    }
  }

  Future<VerificationReportModel> getVerificationReport(String reportId) async {
    try {
      final response = await apiClient.dio.get('/verification-reports/$reportId');
      return VerificationReportModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }
}
