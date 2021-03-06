import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom'
import { useHistory } from 'react-router-dom';
import axios, { AxiosResponse, AxiosError } from 'axios';
import { Layout, Row, Col, Card, Typography, Input, Form, Checkbox, Button } from "antd";
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import Navbar from "../components/Navbar";
import "../css/Login.css"

interface PostLoginRequest {
    username: string
    password: string
}


const Login: React.FC = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState(false);

    const history = useHistory()

    const submitData = (values : any) => {
        axios.post<PostLoginRequest>("/auth/login", {
            username,
            password,
        }).then( (res) => {
            history.push("/")
        }).catch( (err) => {
            setError(true)
        })
    };

    return (
        <Layout>
            <Navbar hideMenu></Navbar>
            <Layout.Content className="site-layout" style={{ padding: '50px 50px', marginTop: 64 }}>
                <Row>
                    <Col xs={0} sm={1} md={4} lg={6} xl={6}> </Col>
                    <Col xs={24} sm={22} md={16} lg={12} xl={12}>
                        <Card title={<Typography.Title level={1} style={{ marginBottom: 0 }}>Login</Typography.Title>}>
                            <Form
                                initialValues={{ remember: true }}
                                onFinish = { submitData }
                            >
                                {/* Username field  */}
                                <Form.Item
                                    name="username"
                                    rules={[{ required: true, message: 'Please input your Username!' }]}
                                >
                                    <Input 
                                        prefix={<UserOutlined className="site-form-item-icon" />} 
                                        placeholder="Username"
                                        onChange = { (e) => setUsername(e.target.value) }
                                    />
                                </Form.Item>

                                {/* Password field */}
                                <Form.Item
                                    name="password"
                                    rules={[{ required: true, message: 'Please input your Password!' }]}
                                    extra = {error && (<Typography.Text type = "danger">Username or Password Incorect</Typography.Text>)}
                                >
                                    <Input
                                        prefix={<LockOutlined className="site-form-item-icon" />}
                                        type="password"
                                        onChange = { (e) => setPassword(e.target.value) }
                                        placeholder="Password"
                                    />
                                </Form.Item>

                                {/* Login/Submit button */}
                                <Form.Item>
                                    <Button type="primary" htmlType="submit" className="login-form-button">
                                        Log in
                                    </Button>
                                </Form.Item>
                            </Form>
                        </Card>
                    </Col>
                    <Col xs={0} sm={1} md={4} lg={6} xl={6}> </Col>
                </Row>
            </Layout.Content>
        </Layout>
    )
}

export default Login