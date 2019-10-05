// Copyright 2019 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Code generated by protoc-gen-go. DO NOT EDIT.
// source: backend/api/pipeline_spec.proto

package go_client // import "github.com/kubeflow/pipelines/backend/api/go_client"

import proto "github.com/golang/protobuf/proto"
import fmt "fmt"
import math "math"

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

// This is a compile-time assertion to ensure that this generated file
// is compatible with the proto package it is being compiled against.
// A compilation error at this line likely means your copy of the
// proto package needs to be updated.
const _ = proto.ProtoPackageIsVersion2 // please upgrade the proto package

type PipelineSpec struct {
	PipelineId           string       `protobuf:"bytes,1,opt,name=pipeline_id,json=pipelineId,proto3" json:"pipeline_id,omitempty"`
	PipelineName         string       `protobuf:"bytes,5,opt,name=pipeline_name,json=pipelineName,proto3" json:"pipeline_name,omitempty"`
	WorkflowManifest     string       `protobuf:"bytes,2,opt,name=workflow_manifest,json=workflowManifest,proto3" json:"workflow_manifest,omitempty"`
	PipelineManifest     string       `protobuf:"bytes,3,opt,name=pipeline_manifest,json=pipelineManifest,proto3" json:"pipeline_manifest,omitempty"`
	Parameters           []*Parameter `protobuf:"bytes,4,rep,name=parameters,proto3" json:"parameters,omitempty"`
	XXX_NoUnkeyedLiteral struct{}     `json:"-"`
	XXX_unrecognized     []byte       `json:"-"`
	XXX_sizecache        int32        `json:"-"`
}

func (m *PipelineSpec) Reset()         { *m = PipelineSpec{} }
func (m *PipelineSpec) String() string { return proto.CompactTextString(m) }
func (*PipelineSpec) ProtoMessage()    {}
func (*PipelineSpec) Descriptor() ([]byte, []int) {
	return fileDescriptor_pipeline_spec_ab99afe9ca6994cc, []int{0}
}
func (m *PipelineSpec) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_PipelineSpec.Unmarshal(m, b)
}
func (m *PipelineSpec) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_PipelineSpec.Marshal(b, m, deterministic)
}
func (dst *PipelineSpec) XXX_Merge(src proto.Message) {
	xxx_messageInfo_PipelineSpec.Merge(dst, src)
}
func (m *PipelineSpec) XXX_Size() int {
	return xxx_messageInfo_PipelineSpec.Size(m)
}
func (m *PipelineSpec) XXX_DiscardUnknown() {
	xxx_messageInfo_PipelineSpec.DiscardUnknown(m)
}

var xxx_messageInfo_PipelineSpec proto.InternalMessageInfo

func (m *PipelineSpec) GetPipelineId() string {
	if m != nil {
		return m.PipelineId
	}
	return ""
}

func (m *PipelineSpec) GetPipelineName() string {
	if m != nil {
		return m.PipelineName
	}
	return ""
}

func (m *PipelineSpec) GetWorkflowManifest() string {
	if m != nil {
		return m.WorkflowManifest
	}
	return ""
}

func (m *PipelineSpec) GetPipelineManifest() string {
	if m != nil {
		return m.PipelineManifest
	}
	return ""
}

func (m *PipelineSpec) GetParameters() []*Parameter {
	if m != nil {
		return m.Parameters
	}
	return nil
}

func init() {
	proto.RegisterType((*PipelineSpec)(nil), "api.PipelineSpec")
}

func init() {
	proto.RegisterFile("backend/api/pipeline_spec.proto", fileDescriptor_pipeline_spec_ab99afe9ca6994cc)
}

var fileDescriptor_pipeline_spec_ab99afe9ca6994cc = []byte{
	// 236 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0xff, 0x54, 0xd0, 0xc1, 0x4a, 0xc3, 0x40,
	0x10, 0x06, 0x60, 0x62, 0x54, 0x70, 0x5a, 0x45, 0x73, 0x0a, 0x7a, 0x68, 0xd1, 0x4b, 0x41, 0xd8,
	0x80, 0xc5, 0x17, 0xf0, 0xe6, 0x41, 0x29, 0xf5, 0xe6, 0x25, 0x4c, 0x36, 0xd3, 0x3a, 0x24, 0xbb,
	0x3b, 0x24, 0x5b, 0xfa, 0xb6, 0x3e, 0x8b, 0x34, 0xed, 0x2e, 0xf1, 0xfa, 0xcf, 0xb7, 0xb3, 0xcc,
	0x0f, 0xb3, 0x0a, 0x75, 0x43, 0xb6, 0x2e, 0x50, 0xb8, 0x10, 0x16, 0x6a, 0xd9, 0x52, 0xd9, 0x0b,
	0x69, 0x25, 0x9d, 0xf3, 0x2e, 0x4b, 0x51, 0xf8, 0xfe, 0xe1, 0x9f, 0xc2, 0x0e, 0x0d, 0x79, 0xea,
	0x8e, 0xe2, 0xf1, 0x37, 0x81, 0xe9, 0xea, 0xf4, 0xf2, 0x4b, 0x48, 0x67, 0x33, 0x98, 0xc4, 0x4d,
	0x5c, 0xe7, 0xc9, 0x3c, 0x59, 0x5c, 0xad, 0x21, 0x44, 0xef, 0x75, 0xf6, 0x04, 0xd7, 0x11, 0x58,
	0x34, 0x94, 0x5f, 0x0c, 0x64, 0x1a, 0xc2, 0x4f, 0x34, 0x94, 0x3d, 0xc3, 0xdd, 0xde, 0x75, 0xcd,
	0xa6, 0x75, 0xfb, 0xd2, 0xa0, 0xe5, 0x0d, 0xf5, 0x3e, 0x3f, 0x1b, 0xe0, 0x6d, 0x18, 0x7c, 0x9c,
	0xf2, 0x03, 0x8e, 0x1b, 0x23, 0x4e, 0x8f, 0x38, 0x0c, 0x22, 0x56, 0x00, 0xf1, 0x86, 0x3e, 0x3f,
	0x9f, 0xa7, 0x8b, 0xc9, 0xcb, 0x8d, 0x42, 0x61, 0xb5, 0x0a, 0xf1, 0x7a, 0x24, 0xde, 0x5e, 0xbf,
	0x97, 0x5b, 0xf6, 0x3f, 0xbb, 0x4a, 0x69, 0x67, 0x8a, 0x66, 0x57, 0xd1, 0xe1, 0xef, 0xd8, 0x56,
	0x5f, 0x8c, 0xdb, 0xd9, 0xba, 0x52, 0xb7, 0x4c, 0xd6, 0x57, 0x97, 0x43, 0x3d, 0xcb, 0xbf, 0x00,
	0x00, 0x00, 0xff, 0xff, 0xeb, 0x6c, 0x41, 0xaf, 0x63, 0x01, 0x00, 0x00,
}
