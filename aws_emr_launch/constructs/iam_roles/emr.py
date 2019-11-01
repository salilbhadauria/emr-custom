# Copyright 2019 Amazon.com, Inc. and its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the 'License').
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#   http://aws.amazon.com/asl/
#
# or in the 'license' file accompanying this file. This file is distributed
# on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from typing import Optional
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    core
)


class EMRRoles(core.Construct):
    def __init__(self, scope: core.Construct, id: str, *, role_name_prefix: Optional[str] = None,
                 artifacts_bucket: Optional[s3.Bucket] = None, logs_bucket: Optional[s3.Bucket] = None) -> None:
        super().__init__(scope, id)

        if role_name_prefix:
            self._service_role = EMRRoles._create_service_role(
                self, 'EMRServiceRole', role_name='{}-ServiceRole'.format(role_name_prefix))
            self._instance_role = EMRRoles._create_instance_role(
                self, 'EMRInstanceRole', role_name='{}-InstanceRole'.format(role_name_prefix))
            self._autoscaling_role = EMRRoles._create_autoscaling_role(
                self, 'EMRAutoScalingRole', role_name='{}-AutoScalingRole'.format(role_name_prefix))

            self._instance_profile = iam.CfnInstanceProfile(
                self, '{}_InstanceProfile'.format(id),
                roles=[self._instance_role.role_name],
                instance_profile_name=self._instance_role.role_name)
            self._instance_profile_arn = self._instance_profile.attr_arn

        if artifacts_bucket:
            artifacts_bucket.grant_read(self._service_role)
            artifacts_bucket.grant_read(self._instance_role)

        if logs_bucket:
            logs_bucket.grant_read_write(self._service_role)
            logs_bucket.grant_read_write(self._instance_role)

    @staticmethod
    def _emr_artifacts_policy() -> iam.PolicyDocument:
        return iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        's3:GetObject*',
                        's3:List*'
                    ],
                    resources=[
                        'arn:aws:s3:::elasticmapreduce',
                        'arn:aws:s3:::elasticmapreduce/*',
                        'arn:aws:s3:::elasticmapreduce.samples',
                        'arn:aws:s3:::elasticmapreduce.samples/*',
                        'arn:aws:s3:::*.elasticmapreduce',
                        'arn:aws:s3:::*.elasticmapreduce/*',
                        'arn:aws:s3:::*.elasticmapreduce.samples',
                        'arn:aws:s3:::*.elasticmapreduce.samples/*'
                    ]
                )
            ]
        )

    @staticmethod
    def _create_service_role(scope: core.Construct, id: str, *, role_name: Optional[str] = None):
        role = iam.Role(scope, id, role_name=role_name,
                        assumed_by=iam.ServicePrincipal('elasticmapreduce.amazonaws.com'),
                        inline_policies={
                            'emr-artifacts-policy': EMRRoles._emr_artifacts_policy()
                        },
                        managed_policies=[
                            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonElasticMapReduceRole')
                        ])
        return role

    @staticmethod
    def _create_autoscaling_role(scope: core.Construct, id: str, *, role_name: Optional[str] = None):
        role = iam.Role(scope, id, role_name=role_name,
                        assumed_by=iam.ServicePrincipal('elasticmapreduce.amazonaws.com'),
                        managed_policies=[
                            iam.ManagedPolicy.from_aws_managed_policy_name(
                                'service-role/AmazonElasticMapReduceforAutoScalingRole')
                        ])

        role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal('application-autoscaling.amazonaws.com')
                ],
                actions=[
                    'sts:AssumeRole'
                ]
            )
        )
        return role

    @staticmethod
    def _create_instance_role(scope: core.Construct, id: str, *, role_name: Optional[str] = None):
        role = iam.Role(scope, id,
                        role_name=role_name,
                        assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
                        inline_policies={
                            'emr-artifacts-policy': EMRRoles._emr_artifacts_policy()
                        })
        return role

    @staticmethod
    def from_role_arns(scope: core.Construct, id: str, service_role_arn: str,
                       instance_role_arn: str, autoscaling_role_arn: str, mutable: Optional[bool] = None):
        roles = EMRRoles(scope, id)
        roles._service_role = iam.Role.from_role_arn(roles, 'EMRServiceRole', service_role_arn, mutable=False)
        roles._instance_role = iam.Role.from_role_arn(roles, 'EMRInstanceRole', instance_role_arn, mutable=mutable)
        roles._autoscaling_role = iam.Role.from_role_arn(
            roles, 'EMRAutoScalingRole', autoscaling_role_arn, mutable=False)
        roles._instance_profile_arn = roles._instance_role.role_arn.replace(':role/', ':instance-profile/')
        return roles

    @property
    def service_role(self) -> iam.Role:
        return self._service_role

    @property
    def instance_role(self) -> iam.Role:
        return self._instance_role

    @property
    def autoscaling_role(self) -> iam.Role:
        return self._autoscaling_role

    @property
    def instance_profile_arn(self) -> str:
        return self._instance_profile_arn
